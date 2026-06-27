from backend.database.connection import get_db
from backend.core.logger import get_logger

logger = get_logger("audit")


def log_action(
    action: str,
    status: str = "SUCCESS",
    employee_id: str | None = None,
    entity: str | None = None,
    entity_id: str | None = None,
    detail: str | None = None,
):
    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO audit_logs
                    (action, status, employee_id, entity, entity_id, detail)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (action, status, employee_id, entity, entity_id, detail))
            conn.commit()
    except Exception as e:
        logger.error(f"Audit log write failed | action={action}: {e}")
