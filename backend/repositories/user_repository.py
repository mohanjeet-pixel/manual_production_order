from backend.database.connection import get_db
from backend.core.logger import get_logger

logger = get_logger("user_repository")


def get_user(employee_id: str) -> dict | None:
    """Return full user record needed for auth and token generation."""
    with get_db() as conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT employee_id, password_hash, role, email, full_name, is_active
                FROM users
                WHERE employee_id = %s
            """, (employee_id,))
            row = cur.fetchone()
            if not row:
                return None
            return {
                "employee_id": row[0],
                "password_hash": row[1],
                "role": row[2],
                "email": row[3],
                "full_name": row[4],
                "is_active": row[5],
            }
        except Exception as e:
            logger.error(f"get_user failed: {e}")
            return None


def get_all_users(include_inactive: bool = False) -> list[dict]:
    with get_db() as conn:
        try:
            cur = conn.cursor()
            query = """
                SELECT employee_id, full_name, email, department, role, is_active, created_at
                FROM users
            """
            if not include_inactive:
                query += " WHERE is_active = TRUE"
            query += " ORDER BY employee_id"
            cur.execute(query)
            rows = cur.fetchall()
            return [
                {
                    "employee_id": r[0],
                    "full_name":   r[1],
                    "email":       r[2],
                    "department":  r[3],
                    "role":        r[4],
                    "is_active":   r[5],
                    "created_at":  str(r[6]),
                }
                for r in rows
            ]
        except Exception as e:
            logger.error(f"get_all_users failed: {e}")
            raise


def create_user(employee_id: str, password_hash: str, full_name: str,
                email: str, department: str | None, role: str) -> None:
    with get_db() as conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO users (employee_id, password_hash, full_name, email, department, role)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (employee_id, password_hash, full_name, email, department, role))
            conn.commit()
            logger.info(f"User created | employee_id={employee_id} role={role}")
        except Exception as e:
            logger.error(f"create_user failed: {e}")
            raise


def update_user(employee_id: str, updates: dict) -> bool:
    allowed = {"full_name", "email", "department", "role", "is_active", "password_hash"}
    fields = {k: v for k, v in updates.items() if k in allowed and v is not None}
    if not fields:
        return False
    with get_db() as conn:
        try:
            cur = conn.cursor()
            set_clause = ", ".join(f"{col} = %s" for col in fields)
            values = list(fields.values()) + [employee_id]
            cur.execute(f"UPDATE users SET {set_clause} WHERE employee_id = %s", values)
            conn.commit()
            logger.info(f"User updated | employee_id={employee_id} fields={list(fields)}")
            return True
        except Exception as e:
            logger.error(f"update_user failed: {e}")
            raise


def deactivate_user(employee_id: str) -> None:
    with get_db() as conn:
        try:
            cur = conn.cursor()
            cur.execute("UPDATE users SET is_active = FALSE WHERE employee_id = %s", (employee_id,))
            conn.commit()
            logger.info(f"User deactivated | employee_id={employee_id}")
        except Exception as e:
            logger.error(f"deactivate_user failed: {e}")
            raise
