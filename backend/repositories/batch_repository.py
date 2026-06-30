from datetime import datetime

from backend.database.connection import get_db
from backend.core.logger import get_logger
from backend.utils.exceptions import BatchNotFoundError

logger = get_logger("batch_repository")


def _generate_batch_id(cur) -> str:
    today = datetime.now().strftime("%Y%m%d")
    prefix = f"BMP{today}"
    cur.execute(
        "SELECT COUNT(*) FROM manual_order_batches WHERE batch_id LIKE %s",
        (f"{prefix}%",)
    )
    count = cur.fetchone()[0]
    return f"{prefix}{count + 1:03d}"


def insert_batch(employee_id: str, total_value: float, token: str, approver: str, remark: str | None = None) -> str:
    with get_db() as conn:
        try:
            cur = conn.cursor()
            batch_id = _generate_batch_id(cur)
            cur.execute("""
                INSERT INTO manual_order_batches
                    (batch_id, employee_id, total_value, status, approval_token, approver_email, remark)
                VALUES (%s, %s, %s, 'PENDING', %s, %s, %s)
            """, (batch_id, employee_id, total_value, token, approver, remark))
            conn.commit()
            logger.info(f"Batch inserted | batch_id={batch_id} employee={employee_id} total={total_value}")
            return batch_id
        except Exception as e:
            logger.error(f"insert_batch failed: {e}")
            raise


def get_batches_by_employee(employee_id: str) -> list[dict]:
    with get_db() as conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT
                    b.batch_id, b.employee_id, b.total_value, b.status,
                    b.created_at, b.approved_at,
                    o.id, o.plant, o.part_no, o.quantity, o.price, o.value,
                    s.api_status, s.sap_order_no
                FROM manual_order_batches b
                LEFT JOIN manual_production_orders o ON o.batch_id = b.batch_id
                LEFT JOIN LATERAL (
                    SELECT api_status, sap_order_no
                    FROM sap_order_results
                    WHERE order_id = o.id
                    ORDER BY id DESC
                    LIMIT 1
                ) s ON TRUE
                WHERE b.employee_id = %s
                ORDER BY b.created_at DESC, o.id
            """, (employee_id,))
            rows = cur.fetchall()

            batches: dict[str, dict] = {}
            for r in rows:
                bid = r[0]
                if bid not in batches:
                    batches[bid] = {
                        "Batch ID":   r[0],
                        "Employee":   r[1],
                        "Total Value": float(r[2]),
                        "Status":     r[3],
                        "Created At": str(r[4])[:10] if r[4] else "",
                        "Approved At": str(r[5])[:10] if r[5] else "",
                        "Orders": [],
                    }
                if r[6] is not None:
                    batches[bid]["Orders"].append({
                        "ID":         r[6],
                        "Plant":      r[7],
                        "Part No":    r[8],
                        "Quantity":   float(r[9]),
                        "Unit Price": float(r[10]),
                        "Value":      float(r[11]),
                        "sap_status":   r[12],
                        "sap_order_no": r[13] or "",
                    })
            return list(batches.values())
        except Exception as e:
            logger.error(f"get_batches_by_employee failed: {e}")
            raise


def get_batch_by_token(token: str) -> dict | None:
    """Return batch header fields for a given approval token."""
    with get_db() as conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT batch_id, employee_id, status, total_value, approver_email, remark
                FROM manual_order_batches
                WHERE approval_token = %s
            """, (token,))
            row = cur.fetchone()
            if not row:
                return None
            return {
                "batch_id":       row[0],
                "employee_id":    row[1],
                "status":         row[2],
                "total_value":    float(row[3]),
                "approver_email": row[4],
                "remark":         row[5] or "",
            }
        except Exception as e:
            logger.error(f"get_batch_by_token failed: {e}")
            raise


def get_batch_items_by_token(token: str) -> list[dict]:
    """Return all line items for a batch action page."""
    with get_db() as conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT o.plant, o.part_no, o.quantity, o.price, o.value
                FROM manual_order_batches b
                JOIN manual_production_orders o ON o.batch_id = b.batch_id
                WHERE b.approval_token = %s
                ORDER BY o.id
            """, (token,))
            return [
                {
                    "plant":    r[0],
                    "part_no":  r[1],
                    "quantity": float(r[2]),
                    "price":    float(r[3]),
                    "value":    float(r[4]),
                }
                for r in cur.fetchall()
            ]
        except Exception as e:
            logger.error(f"get_batch_items_by_token failed: {e}")
            raise


def get_orders_by_batch_token(token: str) -> list[dict]:
    """Return all orders belonging to a batch identified by its approval token."""
    with get_db() as conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT o.id, o.employee_id, o.plant, o.part_no, o.quantity, b.batch_id
                FROM manual_order_batches b
                JOIN manual_production_orders o ON o.batch_id = b.batch_id
                WHERE b.approval_token = %s
            """, (token,))
            rows = cur.fetchall()
            return [
                {
                    "id":          r[0],
                    "employee_id": r[1],
                    "plant":       r[2],
                    "part_no":     r[3],
                    "quantity":    float(r[4]),
                    "batch_id":    r[5],
                }
                for r in rows
            ]
        except Exception as e:
            logger.error(f"get_orders_by_batch_token failed: {e}")
            raise


def update_batch_status(token: str, new_status: str):
    with get_db() as conn:
        try:
            cur = conn.cursor()

            cur.execute("""
                UPDATE manual_order_batches
                SET status = %s, approved_at = NOW()
                WHERE approval_token = %s
                RETURNING batch_id
            """, (new_status, token))
            row = cur.fetchone()
            if not row:
                raise BatchNotFoundError(f"No batch found for token: {token}")
            batch_id = row[0]

            cur.execute("""
                UPDATE manual_production_orders
                SET status = %s, approved_at = NOW()
                WHERE batch_id = %s
            """, (new_status, batch_id))

            conn.commit()
            logger.info(f"Batch status updated | batch_id={batch_id} status={new_status}")
        except Exception as e:
            logger.error(f"update_batch_status failed: {e}")
            raise
