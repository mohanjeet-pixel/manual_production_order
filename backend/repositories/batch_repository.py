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


def insert_batch(employee_id: str, total_value: float, token: str, approver: str) -> str:
    with get_db() as conn:
        try:
            cur = conn.cursor()
            batch_id = _generate_batch_id(cur)
            cur.execute("""
                INSERT INTO manual_order_batches
                    (batch_id, employee_id, total_value, status, approval_token, approver_email)
                VALUES (%s, %s, %s, 'PENDING', %s, %s)
            """, (batch_id, employee_id, total_value, token, approver))
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
                    o.id, o.plant, o.part_no, o.quantity, o.price, o.value
                FROM manual_order_batches b
                LEFT JOIN manual_production_orders o ON o.batch_id = b.batch_id
                WHERE b.employee_id = %s
                ORDER BY b.created_at DESC, o.id
            """, (employee_id,))
            rows = cur.fetchall()

            batches: dict[str, dict] = {}
            for r in rows:
                bid = r[0]
                if bid not in batches:
                    batches[bid] = {
                        "Batch ID": r[0],
                        "Employee": r[1],
                        "Total Value": float(r[2]),
                        "Status": r[3],
                        "Created At": str(r[4]),
                        "Approved At": str(r[5]) if r[5] else "",
                        "Orders": [],
                    }
                if r[6] is not None:
                    batches[bid]["Orders"].append({
                        "ID": r[6],
                        "Plant": r[7],
                        "Part No": r[8],
                        "Quantity": float(r[9]),
                        "Unit Price": float(r[10]),
                        "Value": float(r[11]),
                    })
            return list(batches.values())
        except Exception as e:
            logger.error(f"get_batches_by_employee failed: {e}")
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
