from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.db.session import get_db
from app.core.dependencies import require_authenticated, require_manager_hr_admin
from app.models.onboarding import OnboardingTask
from app.models.employee import Employee
from app.models.user import User
from app.models.communication import Notification
from app.schemas.onboarding import (
    OnboardingTaskCreate,
    OnboardingTaskResponse,
    OnboardingSummaryResponse
)

router = APIRouter(prefix="/onboarding", tags=["Onboarding"])

@router.get("/{employee_id}", response_model=OnboardingSummaryResponse)
def get_employee_onboarding(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated)
):
    """
    Get onboarding checklist and completion rate for an employee.
    Accessible by the employee themselves, their direct manager, or HR/Admin.
    """
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    # Access check
    is_self = (emp.user_id == current_user.id)
    is_mgr = (emp.user and emp.user.manager_id == current_user.id)
    is_hr_admin = (current_user.role.lower() in ["admin", "hr", "superadmin"])

    if not (is_self or is_mgr or is_hr_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Cannot view onboarding records for this employee"
        )

    tasks = db.query(OnboardingTask).filter(
        OnboardingTask.employee_id == employee_id
    ).order_by(OnboardingTask.created_at.asc()).all()

    total = len(tasks)
    completed = sum(1 for t in tasks if t.is_completed)
    rate = round((completed / total) * 100, 1) if total > 0 else 100.0

    return OnboardingSummaryResponse(
        employee_id=emp.id,
        employee_name=emp.user.full_name if emp.user else "Employee",
        total_tasks=total,
        completed_tasks=completed,
        completion_rate_percent=rate,
        tasks=[OnboardingTaskResponse.model_validate(t) for t in tasks]
    )

@router.post("/{employee_id}", response_model=OnboardingTaskResponse, status_code=status.HTTP_201_CREATED)
def add_onboarding_task(
    employee_id: int,
    task_in: OnboardingTaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager_hr_admin)
):
    """
    Assign a new onboarding task to an employee (Manager or HR/Admin).
    """
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    if current_user.role.lower() == "manager":
        if not emp.user or emp.user.manager_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only assign onboarding tasks to your direct reports"
            )

    task = OnboardingTask(
        employee_id=employee_id,
        title=task_in.title,
        description=task_in.description,
        category=task_in.category,
        due_date=task_in.due_date,
        is_completed=False
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return OnboardingTaskResponse.model_validate(task)

@router.put("/tasks/{task_id}/complete", response_model=OnboardingTaskResponse)
def toggle_onboarding_task(
    task_id: int,
    completed: Optional[bool] = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated)
):
    """
    Mark an onboarding task as completed or incomplete.
    """
    task = db.query(OnboardingTask).filter(OnboardingTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    emp = task.employee
    is_self = (emp.user_id == current_user.id)
    is_mgr = (emp.user and emp.user.manager_id == current_user.id)
    is_hr_admin = (current_user.role.lower() in ["admin", "hr", "superadmin"])

    if not (is_self or is_mgr or is_hr_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Not authorized to modify this onboarding task"
        )

    if task.is_completed != bool(completed) and bool(completed) and emp.user and emp.user.manager_id and emp.user_id == current_user.id:
        db.add(Notification(user_id=emp.user.manager_id, title="Onboarding task done", message=f"{emp.user.full_name} completed: {task.title}"))
    task.is_completed = completed
    task.completed_at = datetime.utcnow() if completed else None
    db.commit()
    db.refresh(task)
    return OnboardingTaskResponse.model_validate(task)
