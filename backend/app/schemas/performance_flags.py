from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class ReviewCycleRating(BaseModel):
    review_cycle: str
    rating: int
    feedback: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class PerformanceFlagItem(BaseModel):
    employee_id: int
    employee_code: str
    full_name: str
    job_title: str
    department_id: Optional[int]
    department_name: str
    manager_id: Optional[int]
    manager_name: Optional[str]
    current_rating: int
    previous_ratings: List[ReviewCycleRating]
    consecutive_declines: int
    total_drop: int
    severity: str  # WARNING or CRITICAL
    action_recommendation: str
    attrition_risk_band: Optional[str] = None
    attrition_risk_score: Optional[float] = None

class PerformanceFlagsResponse(BaseModel):
    total_flagged: int
    critical_count: int
    warning_count: int
    flagged_employees: List[PerformanceFlagItem]
    detected_at: datetime
