from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from app.db.session import get_db
from app.core.dependencies import require_manager_hr_admin, require_hr_or_admin
from app.models.user import User
from app.services.ai.performance_flags import get_performance_flagged_employees
from app.schemas.performance_flags import PerformanceFlagsResponse

router = APIRouter(prefix="/ai", tags=["Performance Intelligence"])

@router.get("/performance-flags", response_model=PerformanceFlagsResponse)
def get_performance_flags(
    department_id: Optional[int] = Query(None, description="Filter by department ID (HR/Admin only)"),
    severity: Optional[str] = Query(None, description="Filter by severity: WARNING or CRITICAL"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager_hr_admin)
):
    """
    AI Feature 2: Performance Trend Flagging.
    Detects employees with 2+ consecutive declining performance review ratings.
    - Managers view flags for their direct reports only.
    - HR and Admin view enterprise-wide flags across all departments.
    - Regular employees receive 403 Forbidden.
    """
    filter_mgr_id = None
    if current_user.role.lower() == "manager":
        # Managers are scoped strictly to their direct reports
        filter_mgr_id = current_user.id
        dept_filter = None
    else:
        # HR/Admin can filter by department if provided
        dept_filter = department_id

    flagged_list = get_performance_flagged_employees(
        db=db,
        filter_manager_id=filter_mgr_id,
        filter_department_id=dept_filter,
        filter_severity=severity
    )

    critical_count = sum(1 for f in flagged_list if f.severity == "CRITICAL")
    warning_count = sum(1 for f in flagged_list if f.severity == "WARNING")

    return PerformanceFlagsResponse(
        total_flagged=len(flagged_list),
        critical_count=critical_count,
        warning_count=warning_count,
        flagged_employees=flagged_list,
        detected_at=datetime.utcnow()
    )

class ExitInterviewRequest(BaseModel):
    notes: str = Field(..., min_length=20, max_length=4000)
    job_title: Optional[str] = Field("Software Engineer", max_length=120)
    department: Optional[str] = Field("Software Engineering", max_length=120)

@router.post("/exit-summary")
def summarize_exit_interview_endpoint(
    req: ExitInterviewRequest,
    current_user: User = Depends(require_hr_or_admin)
):
    """
    Bonus Feature (HR/Admin only: exit interviews are sensitive): GenAI synthesis of employee exit interview notes,
    extracting root attrition drivers and preventative recommendations.
    """
    from app.services.genai.bonus_service import summarize_exit_interview
    return summarize_exit_interview(
        notes=req.notes,
        title=req.job_title,
        department=req.department
    )


@router.post("/performance-flags/{employee_id}/one-on-one")
def request_one_on_one(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager_hr_admin)
):
    """Send real in-app notifications asking for a 1-on-1 about a flagged performance decline.
    Managers can only act on their direct reports. (This used to be a button that faked a success toast.)"""
    from app.models.employee import Employee
    from app.models.communication import Notification
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp or not emp.user:
        raise HTTPException(status_code=404, detail="Employee not found")
    if current_user.role.lower() == "manager" and emp.user.manager_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only act on your direct reports")
    flagged = [f for f in get_performance_flagged_employees(db) if f.employee_id == employee_id]
    if not flagged:
        raise HTTPException(status_code=409, detail="This employee is not currently flagged")
    notified = []
    if emp.user.manager_id and emp.user.manager_id != current_user.id:
        db.add(Notification(user_id=emp.user.manager_id, title="1-on-1 requested", message=f"{current_user.full_name} asked for a 1-on-1 with {emp.user.full_name} about recent rating declines."))
        notified.append("their manager")
    db.add(Notification(user_id=emp.user_id, title="Let's talk about your last review", message=f"{current_user.full_name} would like a short 1-on-1 to support you. Nothing to prepare."))
    notified.append(emp.user.full_name)
    db.commit()
    return {"employee_id": employee_id, "notified": notified, "message": f"Notified {' and '.join(notified)}."}
