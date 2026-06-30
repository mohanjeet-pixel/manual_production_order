from backend.database.connection import get_db
from backend.core.logger import get_logger

logger = get_logger("plant_repository")


def get_price_for_part(part_no: str, plant: str) -> float | None:
    """Return price from products where part matches and plant matches plant code."""
    with get_db() as conn:
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT price FROM products WHERE part = %s AND plant = %s AND is_active = TRUE",
                (part_no, plant),
            )
            row = cur.fetchone()
            return float(row[0]) if row else None
        except Exception as e:
            logger.error(f"get_price_for_part failed: {e}")
            raise


def get_parts_for_plant(plant: str) -> list[dict]:
    """Return all active products for a given plant code (for dropdown)."""
    with get_db() as conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT part, description, price
                FROM products
                WHERE plant = %s AND is_active = TRUE
                ORDER BY part
            """, (plant,))
            return [
                {"part_no": r[0], "description": r[1], "price": float(r[2])}
                for r in cur.fetchall()
            ]
        except Exception as e:
            logger.error(f"get_parts_for_plant failed: {e}")
            raise
