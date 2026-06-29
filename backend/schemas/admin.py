from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    employee_id: str
    full_name: str
    email: EmailStr
    department: str | None = None
    role: str = "OPERATOR"
    password: str


class UserUpdate(BaseModel):
    full_name: str | None = None
    email: EmailStr | None = None
    department: str | None = None
    role: str | None = None
    is_active: bool | None = None
    password: str | None = None


class PasswordReset(BaseModel):
    new_password: str


class MatrixCreate(BaseModel):
    level: str
    min_value: float
    max_value: float
    approver_email: EmailStr
    approver_name: str | None = None


class MatrixUpdate(BaseModel):
    level: str | None = None
    min_value: float | None = None
    max_value: float | None = None
    approver_email: EmailStr | None = None
    approver_name: str | None = None
    is_active: bool | None = None


