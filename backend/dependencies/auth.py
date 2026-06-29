from dataclasses import dataclass
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError

from backend.core.security import decode_token

_bearer = HTTPBearer(auto_error=False)

ROLE_OPERATOR = "OPERATOR"
ROLE_MANAGER  = "MANAGER"
ROLE_ADMIN    = "ADMIN"


@dataclass
class CurrentUser:
    employee_id: str
    role: str


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> CurrentUser:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        data = decode_token(credentials.credentials)
        return CurrentUser(employee_id=data["employee_id"], role=data["role"])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_operator(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if user.role not in (ROLE_OPERATOR, ROLE_ADMIN):
        raise HTTPException(status_code=403, detail="Operator access required")
    return user


def require_manager(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if user.role not in (ROLE_MANAGER, ROLE_ADMIN):
        raise HTTPException(status_code=403, detail="Management access required")
    return user


def require_admin(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if user.role != ROLE_ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
