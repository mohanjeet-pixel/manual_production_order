from backend.database.connection import get_db
from backend.core.logger import get_logger

logger = get_logger("product_repository")


def get_part_price(part_no: str) -> float | None:
    with get_db() as conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT price FROM products WHERE part = %s", (part_no,))
            row = cur.fetchone()
            return float(row[0]) if row else None
        except Exception as e:
            logger.error(f"get_part_price failed for '{part_no}': {e}")
            return None
