from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class DepartmentBase(BaseModel):
    name: str = Field(..., max_length=100)
    code: str = Field(..., max_length=20)
    description: Optional[str] = None

class DepartmentCreate(DepartmentBase):
    pass

class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None

class DepartmentResponse(DepartmentBase):
    id: int
    created_at: datetime
    employee_count: Optional[int] = 0

    class Config:
        from_attributes = True

class HierarchyEmployeeNode(BaseModel):
    id: int
    user_id: int
    employee_code: str
    full_name: str
    email: str
    job_title: str
    department: str
    direct_reports: List["HierarchyEmployeeNode"] = []

class HierarchyResponse(BaseModel):
    organization: str
    total_headcount: int
    hierarchy_trees: List[HierarchyEmployeeNode]
