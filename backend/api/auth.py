from fastapi import APIRouter

from backend.schemas.login import LoginRequest, LoginResponse
from backend.database.auth import validate_user
from backend.core.security import create_token

router = APIRouter(tags=["Auth"])


@router.post("/login", response_model=LoginResponse)
def login(data: LoginRequest):
    result = validate_user(data.employee_id, data.password)
    if not result:
        return LoginResponse(success=False, message="Invalid employee ID or password")
    token = create_token(result["employee_id"], result["role"])
    return LoginResponse(
        success=True,
        employee_id=result["employee_id"],
        role=result["role"],
        token=token,
        message="Login successful",
    )
