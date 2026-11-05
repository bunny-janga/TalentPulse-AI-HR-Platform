from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.core.dependencies import require_authenticated, require_hr_or_admin
from app.models.department import Department
from app.models.user import User
from app.models.employee import Employee
from app.schemas.department import (
    DepartmentResponse,
    DepartmentCreate,
    DepartmentUpdate,
    HierarchyResponse,
    HierarchyEmployeeNode
)

router = APIRouter(tags=["Employees & Org"])

@router.get("/departments", response_model=List[DepartmentResponse])
def list_departments(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated)
):
    """List all departments with active employee count."""
    depts = db.query(Department).all()
    results = []
    for d in depts:
        count = db.query(User).filter(User.department_id == d.id, User.is_active == True).count()
        results.append(DepartmentResponse(
            id=d.id,
            name=d.name,
            code=d.code,
            description=d.description,
            created_at=d.created_at,
            employee_count=count
        ))
    return results

@router.post("/departments", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
def create_department(
    dept_in: DepartmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_or_admin)
):
    """Create a new department (Admin/HR only)."""
    existing = db.query(Department).filter(
        (Department.code == dept_in.code.upper()) | (Department.name == dept_in.name)
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Department with code '{dept_in.code}' or name '{dept_in.name}' already exists"
        )
    dept = Department(
        name=dept_in.name,
        code=dept_in.code.upper(),
        description=dept_in.description
    )
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return DepartmentResponse(
        id=dept.id,
        name=dept.name,
        code=dept.code,
        description=dept.description,
        created_at=dept.created_at,
        employee_count=0
    )

@router.get("/departments/{id}", response_model=DepartmentResponse)
def get_department(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated)
):
    """Get single department details."""
    dept = db.query(Department).filter(Department.id == id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    count = db.query(User).filter(User.department_id == dept.id, User.is_active == True).count()
    return DepartmentResponse(
        id=dept.id,
        name=dept.name,
        code=dept.code,
        description=dept.description,
        created_at=dept.created_at,
        employee_count=count
    )

@router.put("/departments/{id}", response_model=DepartmentResponse)
def update_department(
    id: int,
    dept_in: DepartmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_or_admin)
):
    """Update department info (Admin/HR only)."""
    dept = db.query(Department).filter(Department.id == id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    
    if dept_in.name:
        dept.name = dept_in.name
    if dept_in.code:
        dept.code = dept_in.code.upper()
    if dept_in.description is not None:
        dept.description = dept_in.description

    db.commit()
    db.refresh(dept)
    count = db.query(User).filter(User.department_id == dept.id, User.is_active == True).count()
    return DepartmentResponse(
        id=dept.id,
        name=dept.name,
        code=dept.code,
        description=dept.description,
        created_at=dept.created_at,
        employee_count=count
    )

@router.get("/org/hierarchy", response_model=HierarchyResponse)
def get_org_hierarchy(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated)
):
    """
    Get full organizational hierarchy tree showing managers and direct reports.
    """
    all_users = db.query(User).filter(User.is_active == True).all()
    user_map = {u.id: u for u in all_users}
    employee_map = {e.user_id: e for e in db.query(Employee).all()}

    # Group by manager_id
    manager_to_reports = {}
    for u in all_users:
        mgr_id = u.manager_id
        if mgr_id not in manager_to_reports:
            manager_to_reports[mgr_id] = []
        manager_to_reports[mgr_id].append(u)

    def build_node(user: User) -> HierarchyEmployeeNode:
        emp = employee_map.get(user.id)
        node = HierarchyEmployeeNode(
            id=emp.id if emp else user.id,
            user_id=user.id,
            employee_code=emp.employee_code if emp else f"USR-{user.id}",
            full_name=user.full_name,
            email=user.email,
            job_title=emp.job_title if emp else user.role.capitalize(),
            department=user.department.name if user.department else "General",
            direct_reports=[]
        )
        for report in manager_to_reports.get(user.id, []):
            node.direct_reports.append(build_node(report))
        return node

    # Top-level leaders: users with manager_id is None or users with role 'admin'
    top_leaders = [u for u in all_users if u.manager_id is None]
    if not top_leaders:
        top_leaders = [u for u in all_users if u.role == "admin"]

    trees = [build_node(leader) for leader in top_leaders]

    return HierarchyResponse(
        organization="TalentPulse IT Solutions (Visakhapatnam)",
        total_headcount=len(all_users),
        hierarchy_trees=trees
    )
