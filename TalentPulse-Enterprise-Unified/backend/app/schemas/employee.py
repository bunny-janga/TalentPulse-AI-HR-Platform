from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, Field

class EmployeeBase(BaseModel):
    job_title: str
    hire_date: date
    salary: float = Field(..., ge=0)
    salary_band: str = Field(..., description="Low, Medium, or High")
    overtime_status: bool = False
    performance_rating: float = Field(3.0, ge=1.0, le=5.0)
    last_promotion_date: Optional[date] = None
    total_experience_years: float = Field(0.0, ge=0.0)
    years_at_company: float = Field(0.0, ge=0.0)
    location: str = "Visakhapatnam"

class EmployeeCreate(EmployeeBase):
    user_id: int
    employee_code: str

class EmployeeOnboardRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=255)
    email: str = Field(..., min_length=5, max_length=255, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: Optional[str] = Field(None, min_length=8, max_length=128, description="Leave empty to auto-generate a one-time password")
    employee_code: Optional[str] = Field(None, max_length=50)
    job_title: str = Field("Software Engineer", max_length=255)
    department_id: Optional[int] = None
    manager_id: Optional[int] = None
    role: str = "employee"
    salary: float = Field(850000.0, gt=0, le=100000000)
    salary_band: Optional[str] = None
    overtime_status: Optional[bool] = False
    location: str = Field("Visakhapatnam", max_length=255)

class EmployeeUpdate(BaseModel):
    job_title: Optional[str] = Field(None, min_length=2, max_length=255)
    salary: Optional[float] = Field(None, gt=0, le=100000000)
    salary_band: Optional[str] = Field(None, pattern="^(Low|Medium|High)$")
    overtime_status: Optional[bool] = None
    performance_rating: Optional[float] = Field(None, ge=1.0, le=5.0)
    last_promotion_date: Optional[date] = None
    total_experience_years: Optional[float] = Field(None, ge=0, le=60)
    years_at_company: Optional[float] = Field(None, ge=0, le=60)
    location: Optional[str] = Field(None, max_length=255)

class EmployeeResponse(EmployeeBase):
    # Sensitive fields are None when the viewer is not allowed to see them (see routers/employees.py).
    salary: Optional[float] = None
    salary_band: Optional[str] = None
    overtime_status: Optional[bool] = None
    performance_rating: Optional[float] = None
    temporary_password: Optional[str] = None
    id: int
    user_id: int
    employee_code: str
    full_name: str
    email: str
    role: str
    department_id: Optional[int] = None
    department_name: Optional[str] = None
    manager_id: Optional[int] = None
    manager_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
