from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, Field

class LeaveApplyRequest(BaseModel):
    leave_type: str = Field(..., description="One of LEAVE_TYPES, e.g. Casual Leave, Sick Leave, Earned Leave")
    start_date: date
    end_date: date
    days_count: Optional[int] = Field(None, description="Ignored: the server always counts Mon-Fri days itself")
    reason: str = Field(..., min_length=3, max_length=1000)
    employee_id: Optional[int] = Field(None, description="Target employee ID when applied on behalf by HR/Admin/Superadmin")

class LeaveActionRequest(BaseModel):
    comment: Optional[str] = Field("Processed by manager", max_length=500)

class LeaveResponse(BaseModel):
    id: int
    employee_id: int
    employee_name: Optional[str] = None
    employee_code: Optional[str] = None
    department_name: Optional[str] = None
    leave_type: str
    start_date: date
    end_date: date
    days_count: int
    reason: str
    status: str  # PENDING, APPROVED, REJECTED
    approver_id: Optional[int] = None
    approver_name: Optional[str] = None
    approver_comment: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
