from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.db.session import get_db
from app.core.dependencies import require_authenticated, require_manager_hr_admin
from app.models.review import PerformanceReview
from app.models.employee import Employee
from app.models.user import User
from app.models.communication import Notification
from app.schemas.review import (
    ReviewResponse,
    ReviewCreate,
    ReviewUpdate,
    ReviewDraftRequest,
    ReviewDraftNewRequest,
    ReviewDraftResponse
)

router = APIRouter(prefix="/reviews", tags=["Performance Reviews"])

def map_review_response(rev: PerformanceReview) -> ReviewResponse:
    emp = rev.employee
    emp_user = emp.user if emp else None
    reviewer = rev.reviewer
    return ReviewResponse(
        id=rev.id,
        employee_id=rev.employee_id,
        employee_name=emp_user.full_name if emp_user else None,
        employee_code=emp.employee_code if emp else None,
        reviewer_id=rev.reviewer_id,
        reviewer_name=reviewer.full_name if reviewer else None,
        review_cycle=rev.review_cycle,
        rating=rev.rating,
        feedback=rev.feedback,
        strengths=rev.strengths,
        growth_areas=rev.growth_areas,
        goals=rev.goals,
        status=rev.status,
        created_at=rev.created_at,
        updated_at=rev.updated_at
    )

@router.post("", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
def create_review(
    rev_in: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager_hr_admin)
):
    """
    Submit a performance appraisal for an employee (Manager or HR/Admin).
    """
    emp = db.query(Employee).filter(Employee.id == rev_in.employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    # If manager, verify employee reports to them
    if current_user.role.lower() == "manager":
        emp_user = emp.user
        if not emp_user or emp_user.manager_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only conduct reviews for your direct reports"
            )

    if emp.user_id == current_user.id:
        raise HTTPException(status_code=403, detail="You cannot review yourself.")

    dup = db.query(PerformanceReview).filter(
        PerformanceReview.employee_id == rev_in.employee_id,
        PerformanceReview.review_cycle == rev_in.review_cycle
    ).first()
    if dup:
        raise HTTPException(status_code=409, detail=f"A {dup.status.lower()} review for {rev_in.review_cycle} already exists for this employee. Edit it instead.")

    new_rev = PerformanceReview(
        employee_id=rev_in.employee_id,
        reviewer_id=current_user.id,
        review_cycle=rev_in.review_cycle,
        rating=rev_in.rating,
        feedback=rev_in.feedback,
        strengths=rev_in.strengths,
        growth_areas=rev_in.growth_areas,
        goals=rev_in.goals,
        status=rev_in.status or "COMPLETED"
    )
    db.add(new_rev)
    if new_rev.status == "COMPLETED":
        # Drafts must not move the rating that feeds attrition scoring.
        emp.performance_rating = float(rev_in.rating)
        emp.updated_at = datetime.utcnow()
        if emp.user_id:
            db.add(Notification(user_id=emp.user_id, title="New performance review", message=f"{current_user.full_name} published your {rev_in.review_cycle} review ({rev_in.rating}/5)."))

    db.commit()
    db.refresh(new_rev)
    return map_review_response(new_rev)

@router.get("/my", response_model=List[ReviewResponse])
def get_my_reviews(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated)
):
    """
    Get current authenticated user's performance evaluation history given by their manager.
    """
    emp = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not emp:
        return []
    reviews = db.query(PerformanceReview).filter(
        PerformanceReview.employee_id == emp.id,
        PerformanceReview.status == "COMPLETED"   # employees never see a manager's unfinished drafts
    ).order_by(PerformanceReview.created_at.desc()).all()
    return [map_review_response(r) for r in reviews]

@router.get("", response_model=List[ReviewResponse])
def list_all_recent_reviews(
    employee_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated)
):
    """
    List performance reviews:
    - HR / Admin / Superadmin: all evaluations (or filtered by employee)
    - Manager: evaluations for their direct reports
    - Employee: evaluations given to them by their manager
    """
    user_role = current_user.role.lower()
    if user_role in ["admin", "hr", "superadmin"]:
        query = db.query(PerformanceReview)
        if employee_id:
            query = query.filter(PerformanceReview.employee_id == employee_id)
        reviews = query.order_by(PerformanceReview.created_at.desc()).all()
    elif user_role == "manager":
        direct_subquery = db.query(User.id).filter(User.manager_id == current_user.id).subquery()
        emp_subquery = db.query(Employee.id).filter(Employee.user_id.in_(direct_subquery)).subquery()
        query = db.query(PerformanceReview).filter(
            (PerformanceReview.employee_id.in_(emp_subquery)) |
            (PerformanceReview.reviewer_id == current_user.id)
        )
        if employee_id:
            query = query.filter(PerformanceReview.employee_id == employee_id)
        reviews = query.order_by(PerformanceReview.created_at.desc()).all()
    else:
        emp = db.query(Employee).filter(Employee.user_id == current_user.id).first()
        if not emp:
            return []
        reviews = db.query(PerformanceReview).filter(
            PerformanceReview.employee_id == emp.id,
            PerformanceReview.status == "COMPLETED"
        ).order_by(PerformanceReview.created_at.desc()).all()
        
    return [map_review_response(r) for r in reviews]

@router.get("/employee/{id}", response_model=List[ReviewResponse])
def get_employee_reviews(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated)
):
    """
    Get all review cycles for a specific employee.
    Accessible by: HR/Admin/Superadmin, the direct manager, or the employee themselves.
    """
    emp = db.query(Employee).filter(Employee.id == id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    # Access control
    emp_user = emp.user
    user_role = current_user.role.lower()
    is_self = (emp.user_id == current_user.id)
    is_direct_mgr = (emp_user and emp_user.manager_id == current_user.id)
    is_hr_admin = (user_role in ["admin", "hr", "superadmin"])

    if not (is_self or is_direct_mgr or is_hr_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You cannot access performance reviews for this employee"
        )

    q = db.query(PerformanceReview).filter(PerformanceReview.employee_id == id)
    if is_self and not (is_direct_mgr or is_hr_admin):
        q = q.filter(PerformanceReview.status == "COMPLETED")
    reviews = q.order_by(PerformanceReview.created_at.desc()).all()
    return [map_review_response(r) for r in reviews]

@router.put("/{id}", response_model=ReviewResponse)
def update_review(
    id: int,
    rev_in: ReviewUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager_hr_admin)
):
    """
    Update an existing review.
    """
    rev = db.query(PerformanceReview).filter(PerformanceReview.id == id).first()
    if not rev:
        raise HTTPException(status_code=404, detail="Review not found")

    if current_user.role.lower() == "manager" and rev.reviewer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only edit reviews you authored"
        )

    update_data = rev_in.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(rev, field, val)

    if rev.status == "COMPLETED" and rev_in.rating is not None:
        newest = db.query(PerformanceReview).filter(PerformanceReview.employee_id == rev.employee_id, PerformanceReview.status == "COMPLETED").order_by(PerformanceReview.created_at.desc()).first()
        if newest is None or newest.id == rev.id:   # only the latest review drives the employee's current rating
            rev.employee.performance_rating = float(rev_in.rating)

    rev.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(rev)
    return map_review_response(rev)

@router.post("/draft", response_model=ReviewDraftResponse)
def ai_draft_for_employee(
    draft_in: ReviewDraftNewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager_hr_admin)
):
    """GenAI 2: draft a review for an EMPLOYEE before anything is saved. Nothing is persisted; the manager edits and publishes."""
    from app.services.genai.review_draft_service import generate_review_draft_for_employee
    return generate_review_draft_for_employee(
        employee_id=draft_in.employee_id, bullet_notes=draft_in.bullet_notes, review_cycle=draft_in.review_cycle,
        rating=draft_in.rating, current_user=current_user, db=db
    )

@router.post("/{id}/ai-draft", response_model=ReviewDraftResponse)
def ai_draft_performance_review(
    id: int,
    draft_in: ReviewDraftRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager_hr_admin)
):
    """
    GenAI 2: AI-Assisted Performance Review Drafting.
    Transforms manager's raw bullet notes into a structured, professional
    appraisal draft with strengths, growth areas, and future goals.
    The manager can review/edit before saving.
    """
    from app.services.genai.review_draft_service import generate_review_draft
    return generate_review_draft(
        review_id=id,
        bullet_notes=draft_in.bullet_notes,
        current_user=current_user,
        db=db
    )
