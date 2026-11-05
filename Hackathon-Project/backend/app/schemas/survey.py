from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field

class SurveyCreate(BaseModel):
    title: str = Field(..., min_length=4, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    is_active: bool = True

class SurveyResponseCreate(BaseModel):
    score: int = Field(..., ge=1, le=5, description="Rating from 1 (very dissatisfied) to 5 (very satisfied)")
    comments: Optional[str] = Field(None, max_length=1000)

class SurveyStatusUpdate(BaseModel):
    is_active: bool

class SurveyItemResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    is_active: bool
    created_by: Optional[int] = None
    created_at: datetime
    response_count: int = 0
    has_responded: bool = False

    class Config:
        from_attributes = True

class SurveyFeedbackItem(BaseModel):
    id: int
    score: int
    comments: Optional[str]
    sentiment_score: Optional[float]
    sentiment_label: Optional[str]
    created_at: datetime

class SurveyResultsResponse(BaseModel):
    survey_id: int
    title: str
    description: Optional[str]
    is_active: bool
    total_responses: int
    average_score: float
    score_distribution: Dict[str, int]
    sentiment_distribution: Dict[str, int]
    feedback_samples: List[SurveyFeedbackItem] = []
