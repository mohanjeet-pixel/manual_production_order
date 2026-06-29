from backend.database.connection import get_db
from backend.core.logger import get_logger

logger = get_logger("management_repository")


def get_batch_queue(approver_email: str) -> list[dict]:
    """Pending batches waiting for this manager's approval."""
    with get_db() as conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT b.batch_id, b.employee_id, b.total_value, b.status,
                       b.created_at, b.approval_token,
                       COUNT(o.id) AS order_count
                FROM manual_order_batches b
                LEFT JOIN manual_production_orders o ON o.batch_id = b.batch_id
                WHERE b.approver_email = %s AND b.status = 'PENDING'
                GROUP BY b.batch_id, b.employee_id, b.total_value, b.status,
                         b.created_at, b.approval_token
                ORDER BY b.created_at DESC
            """, (approver_email,))
            return [
                {
                    "batch_id":    r[0],
                    "employee_id": r[1],
                    "total_value": float(r[2]),
                    "status":      r[3],
                    "created_at":  str(r[4])[:10] if r[4] else "",
                    "token":       str(r[5]),
                    "order_count": r[6],
                }
                for r in cur.fetchall()
            ]
        except Exception as e:
            logger.error(f"get_batch_queue failed: {e}")
            raise


def get_queue(approver_email: str) -> list[dict]:
    """Pending orders waiting for this manager's approval."""
    with get_db() as conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT id, employee_id, plant, part_no, quantity, price, value,
                       status, approval_token, created_at
                FROM manual_production_orders
                WHERE approver_email = %s AND status = 'PENDING' AND batch_id IS NULL
                ORDER BY id DESC
            """, (approver_email,))
            return [_row_to_dict(r) for r in cur.fetchall()]
        except Exception as e:
            logger.error(f"get_queue failed: {e}")
            raise


def get_history(approver_email: str, status_filter: str | None = None) -> list[dict]:
    """All orders ever routed to this manager."""
    with get_db() as conn:
        try:
            cur = conn.cursor()
            query = """
                SELECT id, employee_id, plant, part_no, quantity, price, value,
                       status, approval_token, created_at
                FROM manual_production_orders
                WHERE approver_email = %s AND batch_id IS NULL
            """
            params: list = [approver_email]
            if status_filter:
                query += " AND status = %s"
                params.append(status_filter)
            query += " ORDER BY id DESC"
            cur.execute(query, params)
            return [_row_to_dict(r) for r in cur.fetchall()]
        except Exception as e:
            logger.error(f"get_history failed: {e}")
            raise


def get_order_for_reapproval(token: str) -> dict | None:
    with get_db() as conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT id, employee_id, plant, part_no, quantity, status,
                       re_approval_count, approver_email
                FROM manual_production_orders
                WHERE approval_token = %s
            """, (token,))
            row = cur.fetchone()
            if not row:
                return None
            return {
                "id":               row[0],
                "employee_id":      row[1],
                "plant":            row[2],
                "part_no":          row[3],
                "quantity":         float(row[4]),
                "status":           row[5],
                "re_approval_count": row[6],
                "approver_email":   row[7],
            }
        except Exception as e:
            logger.error(f"get_order_for_reapproval failed: {e}")
            raise


def mark_reapproved(token: str, approver_email: str) -> None:
    with get_db() as conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                UPDATE manual_production_orders
                SET status = 'APPROVED',
                    re_approval_count = re_approval_count + 1,
                    re_approved_at    = NOW(),
                    re_approved_by    = %s
                WHERE approval_token = %s
            """, (approver_email, token))
            conn.commit()
            logger.info(f"Order re-approved | token={token} by={approver_email}")
        except Exception as e:
            logger.error(f"mark_reapproved failed: {e}")
            raise


def _row_to_dict(r) -> dict:
    return {
        "id":             r[0],
        "employee_id":    r[1],
        "plant":          r[2],
        "part_no":        r[3],
        "quantity":       float(r[4]),
        "unit_price":     float(r[5]),
        "value":          float(r[6]),
        "status":         r[7],
        "token":          str(r[8]) if r[8] else None,
        "created_at":     str(r[9])[:10] if r[9] else "",
    }
