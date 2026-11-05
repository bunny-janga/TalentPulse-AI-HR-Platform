from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date, timedelta

from app.db.session import get_db
from app.core.dependencies import require_authenticated, require_manager_hr_admin
from app.models.leave import LeaveRequest
from app.models.employee import Employee
from app.models.user import User
from app.models.communication import Notification
from app.schemas.leave import LeaveApplyRequest, LeaveActionRequest, LeaveResponse

router = APIRouter(prefix="/leave", tags=["Leave Management"])

LEAVE_TYPES = [
    "Casual Leave", "Sick Leave", "Earned Leave", "Compensatory Off",
    "Bereavement Leave", "Paternity Leave", "Maternity Leave", "Unpaid Leave",
]
# Annual quotas come from the seeded "Leave & Attendance Policy" (12 CL, 10 SL, 15 EL).
ANNUAL_QUOTA = {"Casual Leave": 12, "Sick Leave": 10, "Earned Leave": 15}
SICK_BACKDATE_DAYS = 7


def weekdays_between(start: date, end: date) -> int:
    """Mon-Fri days in [start, end], inclusive."""
    n, d = 0, start
    while d <= end:
        if d.weekday() < 5:
            n += 1
        d += timedelta(days=1)
    return n


def _notify(db: Session, user_id, title: str, message: str):
    if user_id:
        db.add(Notification(user_id=user_id, title=title, message=message))


def _used_days(db: Session, employee_id: int, leave_type: str, year: int, statuses):
    rows = db.query(LeaveRequest).filter(
        LeaveRequest.employee_id == employee_id,
        LeaveRequest.leave_type == leave_type,
        LeaveRequest.status.in_(statuses),
        LeaveRequest.start_date >= date(year, 1, 1),
        LeaveRequest.start_date <= date(year, 12, 31),
    ).all()
    return sum(r.days_count for r in rows)


@router.get("/balance")
def leave_balance(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated)
):
    """Remaining quota for the tracked leave types this calendar year (approved = used, pending = reserved)."""
    year = date.today().year
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    out = []
    for leave_type, quota in ANNUAL_QUOTA.items():
        used = _used_days(db, employee.id, leave_type, year, ["APPROVED"]) if employee else 0
        pending = _used_days(db, employee.id, leave_type, year, ["PENDING"]) if employee else 0
        out.append({"leave_type": leave_type, "quota": quota, "used": used, "pending": pending, "remaining": max(quota - used - pending, 0)})
    return {"year": year, "balances": out}

def map_leave_response(lr: LeaveRequest) -> LeaveResponse:
    emp = lr.employee
    user = emp.user if emp else None
    approver = lr.approver
    return LeaveResponse(
        id=lr.id,
        employee_id=lr.employee_id,
        employee_name=user.full_name if user else None,
        employee_code=emp.employee_code if emp else None,
        department_name=user.department.name if (user and user.department) else None,
        leave_type=lr.leave_type,
        start_date=lr.start_date,
        end_date=lr.end_date,
        days_count=lr.days_count,
        reason=lr.reason,
        status=lr.status,
        approver_id=lr.approver_id,
        approver_name=approver.full_name if approver else None,
        approver_comment=lr.approver_comment,
        created_at=lr.created_at,
        updated_at=lr.updated_at
    )

@router.post("/apply", response_model=LeaveResponse, status_code=status.HTTP_201_CREATED)
def apply_leave(
    leave_in: LeaveApplyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated)
):
    """
    Apply for leave. If HR/Admin/Superadmin specifies an employee_id, apply for that employee.
    Otherwise the employee ID is automatically associated with current user.
    """
    if leave_in.employee_id and current_user.role.lower() in ["admin", "hr", "superadmin"]:
        employee = db.query(Employee).filter(Employee.id == leave_in.employee_id).first()
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Selected target employee with ID #{leave_in.employee_id} not found"
            )
    else:
        employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
        if not employee:
            # Auto-create an employee profile for administrative accounts if missing
            employee = Employee(
                user_id=current_user.id,
                employee_code=f"EMP-{current_user.role[:3].upper()}-{current_user.id:04d}",
                job_title=f"{current_user.role.title()} Executive",
                hire_date=datetime.utcnow().date(),
                salary=1800000.0,
                salary_band="High",
                overtime_status=False,
                performance_rating=4.5,
                total_experience_years=8.0,
                years_at_company=3.0,
                location="Visakhapatnam"
            )
            db.add(employee)
            db.commit()
            db.refresh(employee)

    if leave_in.leave_type not in LEAVE_TYPES:
        raise HTTPException(status_code=422, detail=f"Unknown leave type. Choose one of: {', '.join(LEAVE_TYPES)}")
    if leave_in.end_date < leave_in.start_date:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="End date cannot be earlier than start date")
    if (leave_in.end_date - leave_in.start_date).days > 365:
        raise HTTPException(status_code=422, detail="A single request cannot span more than a year.")

    today = date.today()
    earliest = today - timedelta(days=SICK_BACKDATE_DAYS) if leave_in.leave_type == "Sick Leave" else today
    if leave_in.start_date < earliest:
        raise HTTPException(status_code=422, detail="Only sick leave can be back-dated (up to 7 days).")

    # The server is the source of truth for the day count (clients used to send their own).
    calculated_days = weekdays_between(leave_in.start_date, leave_in.end_date)
    if calculated_days == 0:
        raise HTTPException(status_code=422, detail="That range contains only weekend days.")

    overlap = db.query(LeaveRequest).filter(
        LeaveRequest.employee_id == employee.id,
        LeaveRequest.status.in_(["PENDING", "APPROVED"]),
        LeaveRequest.start_date <= leave_in.end_date,
        LeaveRequest.end_date >= leave_in.start_date,
    ).first()
    if overlap:
        raise HTTPException(status_code=409, detail=f"Overlaps your {overlap.status.lower()} {overlap.leave_type} ({overlap.start_date} to {overlap.end_date}).")

    quota = ANNUAL_QUOTA.get(leave_in.leave_type)
    if quota is not None:
        year = leave_in.start_date.year
        taken = _used_days(db, employee.id, leave_in.leave_type, year, ["APPROVED", "PENDING"])
        if taken + calculated_days > quota:
            raise HTTPException(status_code=409, detail=f"Not enough {leave_in.leave_type} left for {year}: {max(quota - taken, 0)} day(s) remaining, you asked for {calculated_days}.")

    new_leave = LeaveRequest(
        employee_id=employee.id,
        leave_type=leave_in.leave_type,
        start_date=leave_in.start_date,
        end_date=leave_in.end_date,
        days_count=calculated_days,
        reason=leave_in.reason.strip(),
        status="PENDING"
    )
    db.add(new_leave)
    applicant = employee.user
    if applicant and applicant.manager_id:
        _notify(db, applicant.manager_id, "Leave request to review", f"{applicant.full_name} requested {calculated_days} day(s) of {leave_in.leave_type} from {leave_in.start_date}.")
    db.commit()
    db.refresh(new_leave)
    return map_leave_response(new_leave)

@router.put("/{id}/approve", response_model=LeaveResponse)
def approve_leave(
    id: int,
    action_in: Optional[LeaveActionRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager_hr_admin)
):
    """
    Approve a pending leave request (Manager or HR/Admin).
    """
    leave = db.query(LeaveRequest).filter(LeaveRequest.id == id).first()
    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found")

    # If manager, verify the employee reports to them
    if current_user.role.lower() == "manager":
        emp_user = leave.employee.user
        if not emp_user or emp_user.manager_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only approve leave requests for your direct reports"
            )

    if leave.status != "PENDING":
        raise HTTPException(status_code=409, detail=f"This request is already {leave.status.lower()}.")
    if leave.employee and leave.employee.user_id == current_user.id:
        raise HTTPException(status_code=403, detail="You cannot decide your own leave request.")
    leave.status = "APPROVED"
    leave.approver_id = current_user.id
    leave.approver_comment = action_in.comment if action_in else "Approved by manager"
    leave.updated_at = datetime.utcnow()
    if leave.employee and leave.employee.user_id:
        _notify(db, leave.employee.user_id, "Leave approved", f"Your {leave.leave_type} ({leave.start_date} to {leave.end_date}) was approved by {current_user.full_name}.")
    db.commit()
    db.refresh(leave)
    return map_leave_response(leave)

@router.put("/{id}/reject", response_model=LeaveResponse)
def reject_leave(
    id: int,
    action_in: Optional[LeaveActionRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager_hr_admin)
):
    """
    Reject a leave request with manager reason (Manager or HR/Admin).
    """
    leave = db.query(LeaveRequest).filter(LeaveRequest.id == id).first()
    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found")

    if current_user.role.lower() == "manager":
        emp_user = leave.employee.user
        if not emp_user or emp_user.manager_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only process leave requests for your direct reports"
            )

    if leave.status != "PENDING":
        raise HTTPException(status_code=409, detail=f"This request is already {leave.status.lower()}.")
    if leave.employee and leave.employee.user_id == current_user.id:
        raise HTTPException(status_code=403, detail="You cannot decide your own leave request.")
    leave.status = "REJECTED"
    leave.approver_id = current_user.id
    leave.approver_comment = action_in.comment if action_in else "Rejected by manager"
    leave.updated_at = datetime.utcnow()
    if leave.employee and leave.employee.user_id:
        _notify(db, leave.employee.user_id, "Leave rejected", f"Your {leave.leave_type} ({leave.start_date} to {leave.end_date}) was rejected: {leave.approver_comment}")
    db.commit()
    db.refresh(leave)
    return map_leave_response(leave)

@router.get("/my", response_model=List[LeaveResponse])
def get_my_leaves(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated)
):
    """View current user's leave application history."""
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not employee:
        return []
    leaves = db.query(LeaveRequest).filter(
        LeaveRequest.employee_id == employee.id
    ).order_by(LeaveRequest.created_at.desc()).all()
    return [map_leave_response(lr) for lr in leaves]

@router.get("/team", response_model=List[LeaveResponse])
def get_team_leaves(
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated)
):
    """
    View team leave requests:
    - Manager sees direct reports' leaves.
    - HR / Admin sees leaves across all departments.
    - Employee sees their own leaves (graceful fallback).
    """
    if current_user.role.lower() == "employee":
        employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
        if not employee:
            return []
        query = db.query(LeaveRequest).filter(LeaveRequest.employee_id == employee.id)
        if status_filter:
            query = query.filter(LeaveRequest.status == status_filter.upper())
        leaves = query.order_by(LeaveRequest.created_at.desc()).all()
        return [map_leave_response(lr) for lr in leaves]

    query = db.query(LeaveRequest).join(Employee, LeaveRequest.employee_id == Employee.id).join(User, Employee.user_id == User.id)

    if current_user.role.lower() == "manager":
        query = query.filter(User.manager_id == current_user.id)

    if status_filter:
        query = query.filter(LeaveRequest.status == status_filter.upper())

    leaves = query.order_by(LeaveRequest.created_at.desc()).all()
    return [map_leave_response(lr) for lr in leaves]
