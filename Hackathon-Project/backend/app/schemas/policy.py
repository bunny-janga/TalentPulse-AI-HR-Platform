from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field

class PolicyBase(BaseModel):
    title: str = Field(..., max_length=255)
    category: str = Field(..., max_length=100)

class PolicyCreate(PolicyBase):
    text: str

class PolicyResponse(PolicyBase):
    id: int
    file_path: Optional[str] = None
    extracted_text: str = ""
    chunk_count: int = 0
    uploaded_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PolicyDetailResponse(PolicyResponse):
    chunks: List[Any] = []

class ChatAskRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=500, description="Employee question regarding HR policies")

class ChatSourceCitation(BaseModel):
    title: str
    category: str
    snippet: str
    score: Optional[float] = None

class ChatAskResponse(BaseModel):
    query: str
    answer: str
    sources: List[ChatSourceCitation] = []
    mode: Optional[str] = None   # "live" | "offline"
    timestamp: datetime
