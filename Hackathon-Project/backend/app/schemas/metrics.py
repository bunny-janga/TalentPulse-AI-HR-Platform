from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class DepartmentHeadcount(BaseModel):
    department_id: int
    department_name: str
    code: str
    headcount: int
    percentage: float

class LeaveTrendSummary(BaseModel):
    total_requests: int
    approved_count: int
    pending_count: int
    rejected_count: int
    approval_rate_percent: float
    breakdown_by_type: Dict[str, int]

class ReviewCompletionSummary(BaseModel):
    total_reviews_conducted: int
    average_rating: float
    rating_distribution: Dict[str, int]
    flagged_declining_count: int

class AttritionMetricsSummary(BaseModel):
    projected_attrition_rate_percent: float
    industry_benchmark_attrition_percent: float = 22.0
    risk_distribution: Dict[str, int]
    high_risk_headcount: int
    critical_departments: List[str]

class AdminMetricsResponse(BaseModel):
    total_headcount: int
    total_managers: int
    department_headcounts: List[DepartmentHeadcount]
    attrition_summary: AttritionMetricsSummary
    leave_trends: LeaveTrendSummary
    review_metrics: ReviewCompletionSummary
    generated_at: datetime
