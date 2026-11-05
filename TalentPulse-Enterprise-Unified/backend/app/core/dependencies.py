from typing import List, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import decode_access_token
from app.models.user import User
from app.models.employee import Employee

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception

    payload = decode_access_token(token)
    if not payload:
        raise credentials_exception
    
    user_id = payload.get("user_id")
    email = payload.get("sub")
    if user_id is None and email is None:
        raise credentials_exception
        
    query = db.query(User)
    if user_id:
        user = query.filter(User.id == user_id).first()
    else:
        user = query.filter(User.email == email).first()
        
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account"
        )
    return user

def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account"
        )
    return current_user

class RoleChecker:
    """Reusable FastAPI dependency to enforce server-side role-based access control."""
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = [r.lower() for r in allowed_roles]

    def __call__(self, current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role.lower() not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: User role '{current_user.role}' lacks required permissions ({', '.join(self.allowed_roles)})"
            )
        return current_user

def require_roles(*roles: str):
    """Factory creating a role-enforcement dependency."""
    return RoleChecker(list(roles))

# Common role dependencies
require_superadmin = require_roles("superadmin")
require_admin = require_roles("admin", "superadmin")
require_hr_or_admin = require_roles("admin", "superadmin", "hr")
require_manager_hr_admin = require_roles("admin", "superadmin", "hr", "manager")
require_authenticated = get_current_active_user

def check_attrition_access(
    target_employee_id: int,
    current_user: User,
    db: Session
) -> Employee:
    """
    Enforces the HARD RULE:
    Attrition risk is visible ONLY to HR/Admin/Superadmin and the employee's own direct manager.
    Everyone else gets 403 Forbidden.
    """
    employee = db.query(Employee).filter(Employee.id == target_employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    user_role = current_user.role.lower()
    
    # 1. HR, Admin, and Superadmin have full access across the company
    if user_role in ["admin", "superadmin", "hr"]:
        return employee

    # 2. Check if current user is the direct reporting manager of this employee
    # The employee belongs to a user account, whose manager_id may point to current_user.id
    target_user = employee.user
    if target_user and target_user.manager_id == current_user.id:
        return employee

    # 3. Anyone else (including employees themselves or unrelated managers) gets 403
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Forbidden: Attrition risk is accessible only to HR/Admin or the direct reporting manager."
    )
