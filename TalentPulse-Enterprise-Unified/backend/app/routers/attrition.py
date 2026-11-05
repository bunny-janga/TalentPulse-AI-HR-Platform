import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.db.session import get_db
from app.core.dependencies import (
    require_authenticated,
    require_hr_or_admin,
    require_manager_hr_admin,
    check_attrition_access
)
from app.models.employee import Employee
from app.models.user import User
from app.models.department import Department
from app.models.attrition import AttritionScore
from app.services.ai.attrition_service import (
    predict_employee_attrition,
    batch_score_all_employees,
    extract_employee_features,
    actions_for_factors
)
from app.schemas.attrition import (
    AttritionScoreResponse,
    AttritionTeamResponse,
    AttritionDashboardResponse,
    DepartmentRiskSummary,
    BatchRecomputeResponse
)

router = APIRouter(prefix="/attrition", tags=["Attrition Intelligence"])

def format_attrition_response(emp: Employee, score_record: Optional[AttritionScore], db: Session) -> AttritionScoreResponse:
    user = emp.user
    dept_name = user.department.name if (user and user.department) else "General"
    mgr_name = user.manager.full_name if (user and user.manager) else None

    if score_record:
        r_score = score_record.risk_score
        r_band = score_record.risk_band
        try:
            factors = json.loads(score_record.top_factors) if score_record.top_factors else []
        except Exception:
            factors = [score_record.top_factors]
        c_at = score_record.computed_at
    else:
        # Fallback to dynamic computation
        pred = predict_employee_attrition(emp, db)
        r_score = pred["risk_score"]
        r_band = pred["risk_band"]
        factors = pred["top_factors"]
        c_at = datetime.utcnow()
    actions = actions_for_factors(factors) if r_band != "LOW" else []

    features = extract_employee_features(emp, db)

    return AttritionScoreResponse(
        employee_id=emp.id,
        employee_code=emp.employee_code,
        full_name=user.full_name if user else "Employee",
        job_title=emp.job_title,
        department_name=dept_name,
        manager_name=mgr_name,
        risk_score=r_score,
        risk_band=r_band,
        top_factors=factors,
        suggested_actions=actions,
        computed_at=c_at,
        features=features
    )

@router.get("/employee/{id}", response_model=AttritionScoreResponse)
def get_employee_attrition_risk(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated)
):
    """
    HARD RULE ENFORCEMENT:
    Attrition risk is visible ONLY to HR/Admin and the employee's own direct reporting manager.
    Everyone else (including the employee themselves and unrelated managers) receives 403 Forbidden.
    """
    employee = check_attrition_access(id, current_user, db)
    score_record = db.query(AttritionScore).filter(AttritionScore.employee_id == employee.id).first()
    return format_attrition_response(employee, score_record, db)

@router.get("/team", response_model=AttritionTeamResponse)
def get_team_attrition_risk(
    manager_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager_hr_admin)
):
    """
    View team attrition risk for direct reports.
    - Managers can ONLY view their own direct reports.
    - HR/Admin can view any manager's team or their own.
    """
    target_manager_id = current_user.id
    if current_user.role.lower() in ["admin", "hr", "superadmin"] and manager_id:
        target_manager_id = manager_id

    mgr_user = db.query(User).filter(User.id == target_manager_id).first()
    if not mgr_user:
        raise HTTPException(status_code=404, detail="Manager not found")

    # Find direct reports who have employee profiles
    direct_report_users = db.query(User).filter(User.manager_id == target_manager_id, User.is_active == True).all()
    user_ids = [u.id for u in direct_report_users]
    employees = db.query(Employee).filter(Employee.user_id.in_(user_ids)).all()

    team_responses = []
    risk_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}

    for emp in employees:
        score_record = db.query(AttritionScore).filter(AttritionScore.employee_id == emp.id).first()
        res = format_attrition_response(emp, score_record, db)
        team_responses.append(res)
        if res.risk_band in risk_counts:
            risk_counts[res.risk_band] += 1

    team_responses.sort(key=lambda x: x.risk_score, reverse=True)
    return AttritionTeamResponse(
        manager_id=mgr_user.id,
        manager_name=mgr_user.full_name,
        team_size=len(employees),
        risk_counts=risk_counts,
        employees=team_responses
    )

@router.get("/dashboard", response_model=AttritionDashboardResponse)
def get_attrition_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_or_admin)
):
    """
    Aggregated enterprise attrition risk analytics for Leadership and HR.
    Strictly forbidden for Managers and Employees.
    """
    employees = db.query(Employee).all()
    total_headcount = len(employees)
    if total_headcount == 0:
        return AttritionDashboardResponse(
            total_headcount=0,
            projected_attrition_rate=0.0,
            risk_distribution={"HIGH": 0, "MEDIUM": 0, "LOW": 0},
            high_risk_employees=[],
            department_breakdown=[],
            top_company_drivers=[],
            computed_at=datetime.utcnow()
        )

    all_scores = db.query(AttritionScore).all()
    score_map = {s.employee_id: s for s in all_scores}

    risk_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    high_risk_list = []
    all_employee_responses = []
    dept_stats = {}

    for emp in employees:
        s_rec = score_map.get(emp.id)
        res = format_attrition_response(emp, s_rec, db)
        all_employee_responses.append(res)
        band = res.risk_band
        if band in risk_counts:
            risk_counts[band] += 1
        if band == "HIGH":
            high_risk_list.append(res)

        # Department aggregation
        dept_id = emp.user.department_id if (emp.user and emp.user.department_id) else 0
        dept_name = emp.user.department.name if (emp.user and emp.user.department) else "Other"
        if dept_id not in dept_stats:
            dept_stats[dept_id] = {
                "name": dept_name,
                "count": 0,
                "high_count": 0,
                "score_sum": 0.0
            }
        dept_stats[dept_id]["count"] += 1
        dept_stats[dept_id]["score_sum"] += res.risk_score
        if band == "HIGH":
            dept_stats[dept_id]["high_count"] += 1

    dept_summaries = []
    for d_id, st in dept_stats.items():
        avg_score = round(st["score_sum"] / st["count"], 2) if st["count"] > 0 else 0.0
        dept_summaries.append(DepartmentRiskSummary(
            department_id=d_id,
            department_name=st["name"],
            total_staff=st["count"],
            high_risk_count=st["high_count"],
            average_risk_score=avg_score
        ))

    # Sort high risk list and all employees descending by risk score
    high_risk_list.sort(key=lambda x: x.risk_score, reverse=True)
    all_employee_responses.sort(key=lambda x: x.risk_score, reverse=True)

    # Expected attrition = mean predicted probability (the HIGH-band share is a different, bigger-looking number).
    projected_rate = round(sum(r.risk_score for r in all_employee_responses) / total_headcount * 100, 1)

    # Company drivers are counted from what the model actually said about MEDIUM/HIGH-risk staff.
    from collections import Counter
    def _bucket(text: str) -> str:
        t = text.lower()
        for key, label in (("overtime", "Heavy overtime and on-call load"), ("promotion", "Long gaps since last promotion"),
                           ("engagement sentiment", "Low engagement in pulse surveys"), ("declining", "Falling performance ratings"),
                           ("falling review", "Falling performance ratings"), ("entry salary", "Entry-band pay"),
                           ("leave frequency", "Frequent leave requests"), ("low latest", "Low latest performance rating"),
                           ("tenure plateau", "Long-tenure plateau")):
            if key in t:
                return label
        return ""
    counts = Counter()
    for r in all_employee_responses:
        if r.risk_band in ("HIGH", "MEDIUM"):
            for f in r.top_factors:
                label = _bucket(f)
                if label:
                    counts[label] += 1
    top_drivers = [f"{label} ({n} people)" for label, n in counts.most_common(4)]

    return AttritionDashboardResponse(
        total_headcount=total_headcount,
        projected_attrition_rate=projected_rate,
        risk_distribution=risk_counts,
        high_risk_employees=high_risk_list[:15],
        employees=all_employee_responses,
        department_breakdown=dept_summaries,
        top_company_drivers=top_drivers,
        computed_at=datetime.utcnow()
    )

@router.post("/recompute", response_model=BatchRecomputeResponse)
def recompute_attrition_scores(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_or_admin)
):
    """
    Trigger batch ML recomputation of attrition risk for all employees across the company.
    Restricted to HR and Admin.
    """
    result = batch_score_all_employees(db)
    return BatchRecomputeResponse(
        total_scored=result["total_scored"],
        risk_distribution=result["risk_distribution"],
        computed_at=result["computed_at"],
        message="Batch attrition scoring completed successfully"
    )
