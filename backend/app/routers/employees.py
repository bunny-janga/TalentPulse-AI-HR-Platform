from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.db.session import get_db
import secrets
from app.core.security import get_password_hash
from app.models.onboarding import OnboardingTask
from app.models.communication import Notification
from app.core.dependencies import require_authenticated, require_admin, require_hr_or_admin
from app.models.employee import Employee
from app.models.user import User
from app.models.department import Department
from app.schemas.employee import EmployeeResponse, EmployeeCreate, EmployeeUpdate, EmployeeOnboardRequest

router = APIRouter(prefix="/employees", tags=["Employees & Org"])

VALID_ROLES = {"employee", "manager", "hr", "admin", "superadmin"}
HR_ROLES = {"hr", "admin", "superadmin"}
DEFAULT_ONBOARDING = [
    ("Sign the offer letter and employment contract", "HR & Legal", 1),
    ("Collect laptop, ID card and access badge", "IT & Facilities", 2),
    ("Set up corporate email, VPN and Slack", "IT & Facilities", 2),
    ("Read the code of conduct and information-security policy", "Compliance", 5),
    ("Enrol in health insurance and provident fund", "Benefits", 14),
    ("Meet your manager and agree 30-60-90 day goals", "Team", 7),
]


def _temp_password() -> str:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789"
    return "".join(secrets.choice(alphabet) for _ in range(11)) + secrets.choice("!@#$%") + secrets.choice("23456789") + secrets.choice("ABCDEFGHJKLMNPQRSTUVWXYZ")


def map_employee_to_response(emp: Employee, viewer: User = None) -> EmployeeResponse:
    """Map to the API shape, redacting pay and appraisal data the viewer is not entitled to.

    * salary / band: HR, Admin, Super Admin and the employee themself.
    * overtime / rating: the above plus the employee's direct manager.
    """
    user = emp.user
    viewer_role = (viewer.role.lower() if viewer else "")
    is_self = bool(viewer and user and viewer.id == user.id)
    is_manager_of = bool(viewer and user and user.manager_id == viewer.id)
    see_pay = viewer_role in HR_ROLES or is_self
    see_perf = see_pay or is_manager_of
    dept_name = user.department.name if (user and user.department) else None
    mgr_name = user.manager.full_name if (user and user.manager) else None
    
    return EmployeeResponse(
        id=emp.id,
        user_id=emp.user_id,
        employee_code=emp.employee_code,
        job_title=emp.job_title,
        hire_date=emp.hire_date,
        salary=emp.salary if see_pay else None,
        salary_band=emp.salary_band if see_pay else None,
        overtime_status=emp.overtime_status if see_perf else None,
        performance_rating=emp.performance_rating if see_perf else None,
        last_promotion_date=emp.last_promotion_date,
        total_experience_years=emp.total_experience_years,
        years_at_company=emp.years_at_company,
        location=emp.location,
        full_name=user.full_name if user else "Unknown",
        email=user.email if user else "unknown@talentpulse.local",
        role=user.role if user else "employee",
        department_id=user.department_id if user else None,
        department_name=dept_name,
        manager_id=user.manager_id if user else None,
        manager_name=mgr_name,
        created_at=emp.created_at,
        updated_at=emp.updated_at
    )

@router.get("", response_model=List[EmployeeResponse])
def list_employees(
    department_id: Optional[int] = None,
    manager_id: Optional[int] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated)
):
    """
    List all employees with optional filters by department, manager, or name search.
    """
    query = db.query(Employee).join(User, Employee.user_id == User.id)

    if department_id:
        query = query.filter(User.department_id == department_id)
    if manager_id:
        query = query.filter(User.manager_id == manager_id)
    if search:
        search_filter = f"%{search.strip().lower()}%"
        query = query.filter(
            (User.full_name.ilike(search_filter)) |
            (User.email.ilike(search_filter)) |
            (Employee.employee_code.ilike(search_filter)) |
            (Employee.job_title.ilike(search_filter))
        )

    employees = query.order_by(Employee.id.desc()).all()
    return [map_employee_to_response(e, current_user) for e in employees]

@router.get("/{id}", response_model=EmployeeResponse)
def get_employee(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated)
):
    """Get single employee profile by ID."""
    emp = db.query(Employee).filter(Employee.id == id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    return map_employee_to_response(emp, current_user)

@router.post("", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
def create_employee(
    emp_in: EmployeeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Create a new employee profile (Admin & Super Admin only)."""
    user = db.query(User).filter(User.id == emp_in.user_id).first()
    if not user:
        raise HTTPException(status_code=400, detail="User ID does not exist")

    existing_profile = db.query(Employee).filter(
        (Employee.user_id == emp_in.user_id) | (Employee.employee_code == emp_in.employee_code)
    ).first()
    if existing_profile:
        raise HTTPException(status_code=400, detail="Employee profile or code already exists")

    new_emp = Employee(
        user_id=emp_in.user_id,
        employee_code=emp_in.employee_code,
        job_title=emp_in.job_title,
        hire_date=emp_in.hire_date,
        salary=emp_in.salary,
        salary_band=emp_in.salary_band,
        overtime_status=emp_in.overtime_status,
        performance_rating=emp_in.performance_rating,
        last_promotion_date=emp_in.last_promotion_date,
        total_experience_years=emp_in.total_experience_years,
        years_at_company=emp_in.years_at_company,
        location=emp_in.location
    )
    db.add(new_emp)
    db.commit()
    db.refresh(new_emp)
    return map_employee_to_response(new_emp, current_user)

@router.post("/onboard", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
def onboard_new_employee(
    emp_in: EmployeeOnboardRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin)
):
    """
    Unified, atomic onboarding endpoint for Admin and Super Admin:
    Creates or links the User account AND the Employee record in one single database transaction.
    """
    clean_email = emp_in.email.strip().lower()
    clean_name = emp_in.full_name.strip()
    clean_role = emp_in.role.strip().lower()

    if clean_role not in VALID_ROLES - {"superadmin"}:
        raise HTTPException(status_code=422, detail=f"Invalid role '{emp_in.role}'. Use one of: employee, manager, hr, admin.")
    if clean_role == "admin" and current_admin.role.lower() != "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Only Super Admin has higher authority to assign or grant admin access."
        )

    # Department must exist (no silent fallback to "the first department")
    target_dept_id = emp_in.department_id
    if not target_dept_id or not db.query(Department).filter(Department.id == target_dept_id).first():
        raise HTTPException(status_code=422, detail="Choose a valid department.")

    mgr_id = emp_in.manager_id
    if mgr_id:
        mgr = db.query(User).filter(User.id == mgr_id, User.is_active == True).first()  # noqa: E712
        if not mgr:
            raise HTTPException(status_code=422, detail="The chosen manager does not exist or is inactive.")

    if db.query(User).filter(User.email == clean_email).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"An account for '{clean_email}' already exists.")

    # Passwords are stored only as a bcrypt hash. If none is supplied we generate a one-time password
    # and return it once in the response.
    plain_password = emp_in.password or _temp_password()
    user = User(
        email=clean_email,
        hashed_password=get_password_hash(plain_password),
        full_name=clean_name,
        role=clean_role,
        department_id=target_dept_id,
        manager_id=mgr_id,
        is_active=True
    )
    db.add(user)
    db.flush()

    emp_code = emp_in.employee_code.strip() if emp_in.employee_code else None
    if not emp_code or db.query(Employee).filter(Employee.employee_code == emp_code).first():
        n = db.query(Employee).count() + 1
        emp_code = f"EMP-{1000 + n}"
        while db.query(Employee).filter(Employee.employee_code == emp_code).first():
            n += 1
            emp_code = f"EMP-{1000 + n}"

    sal = float(emp_in.salary)
    band = emp_in.salary_band if emp_in.salary_band in ("Low", "Medium", "High") else ("High" if sal >= 1500000 else "Medium" if sal >= 800000 else "Low")
    today = datetime.utcnow().date()

    new_emp = Employee(
        user_id=user.id,
        employee_code=emp_code,
        job_title=emp_in.job_title.strip() if emp_in.job_title else "Software Engineer",
        hire_date=today,
        salary=sal,
        salary_band=band,
        overtime_status=bool(emp_in.overtime_status),
        performance_rating=3.0,
        total_experience_years=0.0,
        years_at_company=0.0,
        location=emp_in.location or "Visakhapatnam"
    )
    db.add(new_emp)
    db.flush()

    # Every new hire gets the standard onboarding checklist.
    from datetime import timedelta
    for title, category, due_days in DEFAULT_ONBOARDING:
        db.add(OnboardingTask(employee_id=new_emp.id, title=title, category=category, due_date=today + timedelta(days=due_days)))
    if mgr_id:
        db.add(Notification(user_id=mgr_id, title="New team member", message=f"{clean_name} has joined your team. Their onboarding checklist is ready."))
    db.commit()
    db.refresh(new_emp)
    resp = map_employee_to_response(new_emp, current_admin)
    if not emp_in.password:
        resp.temporary_password = plain_password
    return resp


@router.put("/{id}", response_model=EmployeeResponse)
def update_employee(
    id: int,
    emp_in: EmployeeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_or_admin)
):
    """Update employee details (HR/Admin only)."""
    emp = db.query(Employee).filter(Employee.id == id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    update_data = emp_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(emp, field, value)

    emp.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(emp)
    return map_employee_to_response(emp, current_user)
