from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Optional

from app.db.session import get_db
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.dependencies import get_current_active_user, require_admin
from app.models.user import User
from app.models.employee import Employee
from app.models.department import Department
from app.models.communication import ChatMessage
from app.schemas.auth import Token, LoginRequest
from app.schemas.user import UserResponse, UserCreate

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=Token)
async def login(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return JWT access token.
    Supports both JSON body ({'email': '...', 'password': '...'})
    and form data for OpenAPI Swagger UI authentication.
    """
    content_type = request.headers.get("content-type", "")
    email = None
    password = None

    if "application/json" in content_type:
        try:
            body = await request.json()
            email = body.get("email") or body.get("username")
            password = body.get("password")
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON payload"
            )
    else:
        try:
            form = await request.form()
            email = form.get("username") or form.get("email")
            password = form.get("password")
        except Exception:
            pass

    if not email or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email and password are required"
        )

    user = db.query(User).filter(User.email == email.strip().lower()).first()
    # Constant-ish work whether or not the user exists, and no plaintext or case-insensitive fallbacks.
    is_valid = bool(user) and verify_password(password, user.hashed_password)

    if not user or not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )

    # Clear policy helpdesk chat history for this user upon every login
    try:
        db.query(ChatMessage).filter(ChatMessage.user_id == user.id).delete()
        db.commit()
    except Exception:
        db.rollback()

    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id, "role": user.role}
    )

    employee = db.query(Employee).filter(Employee.user_id == user.id).first()
    employee_id = employee.id if employee else None

    return Token(
        access_token=access_token,
        token_type="bearer",
        role=user.role,
        user_id=user.id,
        full_name=user.full_name,
        email=user.email,
        employee_id=employee_id
    )

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin)
):
    """
    Create a new user. Only Admin users can create accounts.
    """
    existing_user = db.query(User).filter(User.email == user_in.email.strip().lower()).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists"
        )

    # Requirement 2: Only Super Admin can grant admin access
    if user_in.role.lower() in ["admin", "superadmin"] and current_admin.role.lower() != "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Only Super Admin has higher authority to assign or grant admin access."
        )

    if user_in.department_id:
        dept = db.query(Department).filter(Department.id == user_in.department_id).first()
        if not dept:
            raise HTTPException(status_code=400, detail="Invalid department ID")

    if user_in.manager_id:
        mgr = db.query(User).filter(User.id == user_in.manager_id).first()
        if not mgr:
            raise HTTPException(status_code=400, detail="Invalid manager ID")

    new_user = User(
        email=user_in.email.strip().lower(),
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name.strip(),
        role=user_in.role.strip().lower(),
        department_id=user_in.department_id,
        manager_id=user_in.manager_id,
        is_active=user_in.is_active if user_in.is_active is not None else True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return UserResponse(
        id=new_user.id,
        email=new_user.email,
        full_name=new_user.full_name,
        role=new_user.role,
        department_id=new_user.department_id,
        manager_id=new_user.manager_id,
        is_active=new_user.is_active,
        created_at=new_user.created_at
    )

@router.get("/me", response_model=UserResponse)
def get_current_user_profile(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Return currently authenticated user profile with department, manager, and employee details.
    """
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    
    resp = UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        department_id=current_user.department_id,
        manager_id=current_user.manager_id,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        department=current_user.department,
        manager=current_user.manager,
        employee_id=employee.id if employee else None,
        job_title=employee.job_title if employee else None
    )
    return resp
