from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class AttritionScoreResponse(BaseModel):
    employee_id: int
    employee_code: str
    full_name: str
    job_title: str
    department_name: Optional[str] = None
    manager_name: Optional[str] = None
    risk_score: float
    risk_band: str  # LOW, MEDIUM, HIGH
    top_factors: List[str]
    suggested_actions: List[str] = []
    computed_at: datetime
    features: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

class AttritionTeamResponse(BaseModel):
    manager_id: int
    manager_name: str
    team_size: int
    risk_counts: Dict[str, int]
    employees: List[AttritionScoreResponse]

class DepartmentRiskSummary(BaseModel):
    department_id: int
    department_name: str
    total_staff: int
    high_risk_count: int
    average_risk_score: float

class AttritionDashboardResponse(BaseModel):
    total_headcount: int
    projected_attrition_rate: float
    risk_distribution: Dict[str, int]
    high_risk_employees: List[AttritionScoreResponse]
    employees: List[AttritionScoreResponse] = []
    department_breakdown: List[DepartmentRiskSummary]
    top_company_drivers: List[str]
    computed_at: datetime

class BatchRecomputeResponse(BaseModel):
    total_scored: int
    risk_distribution: Dict[str, int]
    computed_at: str
    message: str = "Batch attrition scoring completed successfully"
