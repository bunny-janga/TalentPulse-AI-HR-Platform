from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.employee import Employee
from app.models.review import PerformanceReview
from app.models.user import User
from app.models.attrition import AttritionScore
from app.schemas.performance_flags import PerformanceFlagItem, ReviewCycleRating

def evaluate_employee_performance_trend(
    employee: Employee,
    reviews: List[PerformanceReview],
    attrition_score: Optional[AttritionScore] = None
) -> Optional[PerformanceFlagItem]:
    """
    Evaluates whether an employee has 2 or more consecutive declining review ratings.
    Returns PerformanceFlagItem if flagged, else None.
    """
    if len(reviews) < 3:
        return None

    # Sort reviews chronologically (oldest to newest)
    sorted_reviews = sorted(reviews, key=lambda r: r.created_at)

    ratings = [r.rating for r in sorted_reviews]
    # Check consecutive declines at the tail of the review series
    consecutive_drops = 0
    for i in range(len(ratings) - 1, 0, -1):
        if ratings[i] < ratings[i - 1]:
            consecutive_drops += 1
        else:
            break

    # AI Feature 2 Rule: 2+ consecutive declining review ratings
    if consecutive_drops < 2:
        return None

    current_rating = ratings[-1]
    initial_rating = ratings[-1 - consecutive_drops]
    total_drop = initial_rating - current_rating

    # Severity classification
    if current_rating <= 2 or total_drop >= 2:
        severity = "CRITICAL"
        recommendation = (
            "Initiate immediate 1-on-1 performance intervention and structured 30-day PIP. "
            "Examine workload, overtime hours, and project alignment."
        )
    else:
        severity = "WARNING"
        recommendation = (
            "Schedule quarterly performance check-in. Review recent sprint velocity, "
            "technical hurdles, and provide peer mentoring."
        )

    user = employee.user
    dept_id = user.department_id if user else None
    dept_name = user.department.name if (user and user.department) else "General"
    mgr_id = user.manager_id if user else None
    mgr_name = user.manager.full_name if (user and user.manager) else None

    history_items = [
        ReviewCycleRating(
            review_cycle=r.review_cycle,
            rating=r.rating,
            feedback=r.feedback,
            created_at=r.created_at
        )
        for r in sorted_reviews
    ]

    r_band = attrition_score.risk_band if attrition_score else None
    r_score = attrition_score.risk_score if attrition_score else None

    return PerformanceFlagItem(
        employee_id=employee.id,
        employee_code=employee.employee_code,
        full_name=user.full_name if user else "Employee",
        job_title=employee.job_title,
        department_id=dept_id,
        department_name=dept_name,
        manager_id=mgr_id,
        manager_name=mgr_name,
        current_rating=current_rating,
        previous_ratings=history_items,
        consecutive_declines=consecutive_drops,
        total_drop=total_drop,
        severity=severity,
        action_recommendation=recommendation,
        attrition_risk_band=r_band,
        attrition_risk_score=r_score
    )

def get_performance_flagged_employees(
    db: Session,
    filter_manager_id: Optional[int] = None,
    filter_department_id: Optional[int] = None,
    filter_severity: Optional[str] = None
) -> List[PerformanceFlagItem]:
    """
    Retrieves all employees with 2+ consecutive declining reviews.
    Can be scoped by manager (for manager portal) or department.
    """
    query = db.query(Employee).join(User, Employee.user_id == User.id)

    if filter_manager_id:
        query = query.filter(User.manager_id == filter_manager_id)
    if filter_department_id:
        query = query.filter(User.department_id == filter_department_id)

    employees = query.all()

    # Pre-fetch attrition scores
    scores = {s.employee_id: s for s in db.query(AttritionScore).all()}

    flagged = []
    for emp in employees:
        reviews = db.query(PerformanceReview).filter(PerformanceReview.employee_id == emp.id, PerformanceReview.status == "COMPLETED").all()
        flag_item = evaluate_employee_performance_trend(emp, reviews, scores.get(emp.id))
        if flag_item:
            if filter_severity and flag_item.severity.upper() != filter_severity.upper():
                continue
            flagged.append(flag_item)

    # Sort critical first, then total drop descending
    flagged.sort(key=lambda x: (0 if x.severity == "CRITICAL" else 1, -x.total_drop))
    return flagged
