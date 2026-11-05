from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class UserBase(BaseModel):
    email: str = Field(..., description="Corporate email address")
    full_name: str
    role: str  # admin, hr, manager, employee
    department_id: Optional[int] = None
    manager_id: Optional[int] = None
    is_active: Optional[bool] = True

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    department_id: Optional[int] = None
    manager_id: Optional[int] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None

class DepartmentSimple(BaseModel):
    id: int
    name: str
    code: str

    class Config:
        from_attributes = True

class ManagerSimple(BaseModel):
    id: int
    full_name: str
    email: str

    class Config:
        from_attributes = True

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    department_id: Optional[int] = None
    manager_id: Optional[int] = None
    is_active: bool
    created_at: datetime
    department: Optional[DepartmentSimple] = None
    manager: Optional[ManagerSimple] = None
    employee_id: Optional[int] = None
    job_title: Optional[str] = None

    class Config:
        from_attributes = True
