from backend.database.connection import get_db
from backend.core.logger import get_logger

logger = get_logger("order_repository")


def insert_order(
    employee_id: str,
    plant: str,
    part_no: str,
    quantity: float,
    value: float,
    price: float,
    status: str,
    token: str | None = None,
    approver: str | None = None,
    batch_id: str | None = None,
):
    with get_db() as conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO manual_production_orders
                    (employee_id, plant, part_no, quantity, value, price,
                     status, approval_token, approver_email, batch_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (employee_id, plant, part_no, quantity, value, price, status, token, approver, batch_id))
            conn.commit()
            logger.info(f"Order inserted | employee={employee_id} part={part_no} value={value} batch={batch_id}")
        except Exception as e:
            logger.error(f"insert_order failed: {e}")
            raise


def get_orders_by_employee(employee_id: str) -> list[dict]:
    with get_db() as conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT o.id, o.employee_id, o.plant, o.part_no, o.quantity, o.price, o.value,
                       COALESCE(o.status, 'PENDING'), o.approved_by, o.approved_at,
                       o.batch_id, o.created_at,
                       s.api_status, s.sap_order_no, s.error_detail, s.messages
                FROM manual_production_orders o
                LEFT JOIN sap_order_results s ON s.order_id = o.id
                WHERE o.employee_id = %s
                ORDER BY o.id DESC
            """, (employee_id,))
            rows = cur.fetchall()
            return [
                {
                    "ID":          r[0],
                    "Employee":    r[1],
                    "Plant":       r[2],
                    "Part No":     r[3],
                    "Quantity":    r[4],
                    "Unit Price":  r[5],
                    "Value":       r[6],
                    "Status":      r[7],
                    "Approved By": r[8] or "",
                    "Approved At": str(r[9]) if r[9] else "",
                    "batch_id":    r[10] or "",
                    "created_at":  str(r[11])[:10] if r[11] else "",
                    "sap_status":    r[12],
                    "sap_order_no":  r[13] or "",
                    "sap_error":     r[14] or "",
                    "sap_messages":  r[15] if r[15] else "[]",
                }
                for r in rows
            ]
        except Exception as e:
            logger.error(f"get_orders_by_employee failed: {e}")
            raise


def get_order_by_token(token: str) -> dict | None:
    with get_db() as conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT id, employee_id, plant, part_no, quantity
                FROM manual_production_orders
                WHERE approval_token = %s
            """, (token,))
            row = cur.fetchone()
            if not row:
                return None
            return {
                "id":          row[0],
                "employee_id": row[1],
                "plant":       row[2],
                "part_no":     row[3],
                "quantity":    float(row[4]),
            }
        except Exception as e:
            logger.error(f"get_order_by_token failed: {e}")
            raise


def update_order_status(token: str, new_status: str):
    with get_db() as conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                UPDATE manual_production_orders
                SET status = %s, approved_at = NOW()
                WHERE approval_token = %s
            """, (new_status, token))
            conn.commit()
            logger.info(f"Order status updated | token={token} status={new_status}")
        except Exception as e:
            logger.error(f"update_order_status failed: {e}")
            raise
