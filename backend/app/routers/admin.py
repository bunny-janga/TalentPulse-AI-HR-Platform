from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Dict, List

from app.db.session import get_db
from pydantic import BaseModel
from app.core.security import verify_password, get_password_hash
from app.core.dependencies import require_hr_or_admin, require_admin, require_superadmin
from app.models.user import User
from app.models.employee import Employee
from app.models.department import Department
from app.models.leave import LeaveRequest
from app.models.review import PerformanceReview
from app.models.attrition import AttritionScore
from app.services.ai.performance_flags import get_performance_flagged_employees
from app.schemas.metrics import (
    AdminMetricsResponse,
    DepartmentHeadcount,
    LeaveTrendSummary,
    ReviewCompletionSummary,
    AttritionMetricsSummary
)

router = APIRouter(prefix="/admin", tags=["Admin Metrics"])

@router.get("/metrics", response_model=AdminMetricsResponse)
def get_workforce_admin_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_or_admin)
):
    """
    Workforce analytics dashboard for Leadership and HR Operations:
    1. Headcount by department and organization percentages.
    2. Annualized attrition rate vs Visakhapatnam IT benchmark (22%).
    3. Leave trends (approval rate and type breakdowns).
    4. Performance review metrics, average rating, and declining review alerts.
    5. Attrition risk distribution and critical departments.
    """
    # Headcount = active accounts, the same population the department split uses (they used to disagree).
    total_employees = db.query(User).filter(User.is_active == True).count() or 1  # noqa: E712 (avoid div by zero)

    # 1. Headcount by department
    departments = db.query(Department).all()
    dept_headcounts = []
    for d in departments:
        count = db.query(User).filter(User.department_id == d.id, User.is_active == True).count()
        pct = round((count / total_employees) * 100, 1)
        dept_headcounts.append(DepartmentHeadcount(
            department_id=d.id,
            department_name=d.name,
            code=d.code,
            headcount=count,
            percentage=pct
        ))

    # 2. Total managers
    manager_count = db.query(User).filter(User.role == "manager", User.is_active == True).count()

    # 3. Leave trends
    total_leaves = db.query(LeaveRequest).count()
    approved_leaves = db.query(LeaveRequest).filter(LeaveRequest.status == "APPROVED").count()
    pending_leaves = db.query(LeaveRequest).filter(LeaveRequest.status == "PENDING").count()
    rejected_leaves = db.query(LeaveRequest).filter(LeaveRequest.status == "REJECTED").count()
    approval_rate = round((approved_leaves / total_leaves) * 100, 1) if total_leaves > 0 else 0.0

    all_leaves = db.query(LeaveRequest).all()
    type_counts: Dict[str, int] = {}
    for l in all_leaves:
        type_counts[l.leave_type] = type_counts.get(l.leave_type, 0) + 1

    leave_summary = LeaveTrendSummary(
        total_requests=total_leaves,
        approved_count=approved_leaves,
        pending_count=pending_leaves,
        rejected_count=rejected_leaves,
        approval_rate_percent=approval_rate,
        breakdown_by_type=type_counts
    )

    # 4. Review completion & performance ratings
    all_reviews = db.query(PerformanceReview).filter(PerformanceReview.status == "COMPLETED").all()
    total_reviews = len(all_reviews)
    avg_rating = round(sum(r.rating for r in all_reviews) / total_reviews, 2) if total_reviews > 0 else 0.0
    rating_dist = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
    for r in all_reviews:
        k = str(r.rating)
        if k in rating_dist:
            rating_dist[k] += 1

    flagged_employees = get_performance_flagged_employees(db)

    review_summary = ReviewCompletionSummary(
        total_reviews_conducted=total_reviews,
        average_rating=avg_rating,
        rating_distribution=rating_dist,
        flagged_declining_count=len(flagged_employees)
    )

    # 5. Attrition metrics summary
    attrition_scores = db.query(AttritionScore).all()
    risk_dist = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    high_risk_depts: Dict[str, int] = {}

    for s in attrition_scores:
        band = s.risk_band or "LOW"
        if band in risk_dist:
            risk_dist[band] += 1
        if band == "HIGH":
            emp = s.employee
            if emp and emp.user and emp.user.department:
                d_name = emp.user.department.name
                high_risk_depts[d_name] = high_risk_depts.get(d_name, 0) + 1

    high_count = risk_dist["HIGH"]
    # Expected attrition = average predicted probability across scored staff (not the share of HIGH-band people).
    projected_attr_rate = round((sum((x.risk_score or 0.0) for x in attrition_scores) / len(attrition_scores)) * 100, 1) if attrition_scores else 0.0

    crit_depts = sorted(high_risk_depts.keys(), key=lambda d: high_risk_depts[d], reverse=True)[:3]

    attrition_summary = AttritionMetricsSummary(
        projected_attrition_rate_percent=projected_attr_rate,
        industry_benchmark_attrition_percent=22.0,
        risk_distribution=risk_dist,
        high_risk_headcount=high_count,
        critical_departments=crit_depts
    )

    return AdminMetricsResponse(
        total_headcount=total_employees,
        total_managers=manager_count,
        department_headcounts=dept_headcounts,
        attrition_summary=attrition_summary,
        leave_trends=leave_summary,
        review_metrics=review_summary,
        generated_at=datetime.utcnow()
    )


class RoleUpdateRequest(BaseModel):
    role: str

@router.get("/users")
def list_system_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    List all registered user accounts with their role and admin authority category.
    Available to Admin and Super Admin.
    """
    users = db.query(User).order_by(User.id.desc()).all()
    result = []
    for u in users:
        dept_name = u.department.name if u.department else "None"
        is_super = u.role.lower() == "superadmin"
        is_adm = u.role.lower() in ["admin", "superadmin"]
        result.append({
            "id": u.id,
            "full_name": u.full_name,
            "email": u.email,
            "role": u.role,
            "department": dept_name,
            "is_active": u.is_active,
            "is_admin": is_adm,
            "is_superadmin": is_super,
            "authority_category": "Higher Authority (Super Admin)" if is_super else ("Administrator" if is_adm else "Standard User")
        })
    return {
        "total_users": len(result),
        "can_assign_authority": current_user.role.lower() == "superadmin",
        "current_user_role": current_user.role,
        "users": result
    }

@router.put("/users/{user_id}/role")
def update_user_role(
    user_id: int,
    req: RoleUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superadmin)
):
    """
    Requirement 2: Admin should have a separate category of higher authority (Super Admin)
    so he can give admin access, and only Super Admin can control the assigning authority.
    Strictly enforced by require_superadmin dependency.
    """
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    new_role = req.role.strip().lower()
    valid_roles = ["superadmin", "admin", "hr", "manager", "employee"]
    if new_role not in valid_roles:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role '{new_role}'. Valid roles are: {', '.join(valid_roles)}"
        )

    # Prevent demoting the last superadmin
    if target_user.role.lower() == "superadmin" and new_role != "superadmin":
        super_count = db.query(User).filter(User.role == "superadmin", User.is_active == True).count()
        if super_count <= 1:
            raise HTTPException(
                status_code=400,
                detail="Cannot demote the only active Super Admin account"
            )

    old_role = target_user.role
    target_user.role = new_role
    db.commit()

    return {
        "message": f"Successfully updated {target_user.full_name}'s role from '{old_role}' to '{new_role}'.",
        "user_id": target_user.id,
        "email": target_user.email,
        "role": target_user.role,
        "is_admin": new_role in ["admin", "superadmin"],
        "assigned_by": current_user.email
    }


def _temp_password() -> str:
    """Random one-time password: 14 chars, mixed classes, no ambiguous characters."""
    import secrets
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789"
    core = "".join(secrets.choice(alphabet) for _ in range(11))
    return f"{core}{secrets.choice('!@#$%')}{secrets.choice('23456789')}{secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ')}"


@router.post("/users/{user_id}/reset-password")
def reset_user_password(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Issue a new one-time password (shown once, stored only as a bcrypt hash). Replaces the old plaintext vault."""
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if target.role in ("admin", "superadmin") and current_user.role != "superadmin":
        raise HTTPException(status_code=403, detail="Only the Super Admin can reset an admin's password.")
    new_pw = _temp_password()
    target.hashed_password = get_password_hash(new_pw)
    db.commit()
    return {"user_id": target.id, "email": target.email, "temporary_password": new_pw}
