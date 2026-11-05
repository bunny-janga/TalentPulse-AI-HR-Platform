from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field

class OnboardingTaskCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    category: str = Field("General", max_length=100)
    due_date: Optional[date] = None

class OnboardingTaskResponse(BaseModel):
    id: int
    employee_id: int
    title: str
    description: Optional[str] = None
    category: str
    due_date: Optional[date] = None
    is_completed: bool
    completed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class OnboardingSummaryResponse(BaseModel):
    employee_id: int
    employee_name: str
    total_tasks: int
    completed_tasks: int
    completion_rate_percent: float
    tasks: List[OnboardingTaskResponse]
