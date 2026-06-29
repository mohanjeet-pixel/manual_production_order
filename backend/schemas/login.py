from pydantic import BaseModel


class LoginRequest(BaseModel):
    employee_id: str
    password: str


class LoginResponse(BaseModel):
    success: bool
    employee_id: str | None = None
    role: str | None = None
    token: str | None = None
    message: str = ""
