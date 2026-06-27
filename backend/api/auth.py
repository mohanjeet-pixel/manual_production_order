from fastapi import APIRouter

from backend.schemas.login import LoginRequest, LoginResponse
from backend.database.auth import validate_user
from backend.core.security import create_token

router = APIRouter(tags=["Auth"])


@router.post("/login", response_model=LoginResponse)
def login(data: LoginRequest):
    success = validate_user(data.employee_id, data.password)
    if not success:
        return LoginResponse(success=False, message="Invalid employee ID or password")
    token = create_token(data.employee_id)
    return LoginResponse(
        success=True,
        employee_id=data.employee_id,
        token=token,
        message="Login successful",
    )
