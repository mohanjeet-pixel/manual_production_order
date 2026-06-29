from datetime import datetime, timedelta, timezone
import bcrypt
from jose import JWTError, jwt

from backend.core.config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRE_MINUTES


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_token(employee_id: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    payload = {"sub": employee_id, "role": role, "exp": expire}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Returns {"employee_id": str, "role": str}."""
    payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    employee_id: str = payload.get("sub")
    role: str = payload.get("role", "OPERATOR")
    if not employee_id:
        raise JWTError("Token missing subject")
    return {"employee_id": employee_id, "role": role}
