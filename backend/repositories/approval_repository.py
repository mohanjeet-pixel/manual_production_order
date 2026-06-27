from backend.database.connection import get_db
from backend.core.logger import get_logger
from backend.utils.exceptions import ApproverNotFoundError

logger = get_logger("approval_repository")


def get_approver_email(value: float) -> str:
    with get_db() as conn:
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT approver_email FROM approval_matrix WHERE %s BETWEEN min_value AND max_value",
                (value,)
            )
            row = cur.fetchone()
            if row:
                return row[0]
            raise ApproverNotFoundError(f"No approver configured for value {value}")
        except Exception as e:
            logger.error(f"get_approver_email failed: {e}")
            raise
