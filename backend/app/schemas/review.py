from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class ReviewCreate(BaseModel):
    employee_id: int
    review_cycle: str = Field(..., pattern=r"^\d{4}-H[12]$", description="e.g. 2025-H1, 2026-H2")
    rating: int = Field(..., ge=1, le=5)
    feedback: Optional[str] = Field(None, max_length=4000)
    strengths: Optional[str] = Field(None, max_length=4000)
    growth_areas: Optional[str] = Field(None, max_length=4000)
    goals: Optional[str] = Field(None, max_length=4000)
    status: Optional[str] = Field("COMPLETED", pattern="^(DRAFT|COMPLETED)$")

class ReviewUpdate(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5)
    feedback: Optional[str] = None
    strengths: Optional[str] = None
    growth_areas: Optional[str] = None
    goals: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(DRAFT|COMPLETED)$")

class ReviewDraftRequest(BaseModel):
    bullet_notes: str = Field(..., min_length=10, max_length=3000, description="Short bullet notes from the manager on employee performance")

class ReviewDraftNewRequest(ReviewDraftRequest):
    employee_id: int
    review_cycle: Optional[str] = Field(None, pattern=r"^\d{4}-H[12]$")
    rating: Optional[int] = Field(None, ge=1, le=5)

class ReviewDraftResponse(BaseModel):
    draft_review: str
    summary: str = ""
    strengths: str = ""
    growth_areas: str = ""
    goals: str = ""
    mode: str = "offline"   # "live" when an LLM wrote it, "offline" when only the manager's own notes were re-filed

class ReviewResponse(BaseModel):
    id: int
    employee_id: int
    employee_name: Optional[str] = None
    employee_code: Optional[str] = None
    reviewer_id: int
    reviewer_name: Optional[str] = None
    review_cycle: str
    rating: int
    feedback: Optional[str] = None
    strengths: Optional[str] = None
    growth_areas: Optional[str] = None
    goals: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
