from backend.database.connection import get_db
from backend.core.logger import get_logger

logger = get_logger("user_repository")


def get_user(employee_id: str):
    with get_db() as conn:
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT employee_id, password FROM users WHERE employee_id = %s",
                (employee_id,)
            )
            return cur.fetchone()
        except Exception as e:
            logger.error(f"get_user failed: {e}")
            return None
