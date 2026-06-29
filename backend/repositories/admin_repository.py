from backend.database.connection import get_db
from backend.core.logger import get_logger

logger = get_logger("admin_repository")


# ── Approval Matrix ───────────────────────────────────────────

def get_matrix() -> list[dict]:
    with get_db() as conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT id, level, min_value, max_value, approver_name, approver_email, is_active
                FROM approval_matrix
                ORDER BY min_value
            """)
            return [
                {
                    "id":             r[0],
                    "level":          r[1],
                    "min_value":      float(r[2]),
                    "max_value":      float(r[3]),
                    "approver_name":  r[4],
                    "approver_email": r[5],
                    "is_active":      r[6],
                }
                for r in cur.fetchall()
            ]
        except Exception as e:
            logger.error(f"get_matrix failed: {e}")
            raise


def update_matrix_entry(entry_id: int, updates: dict) -> None:
    allowed = {"min_value", "max_value", "approver_name", "approver_email", "is_active", "level"}
    fields = {k: v for k, v in updates.items() if k in allowed and v is not None}
    if not fields:
        return
    with get_db() as conn:
        try:
            cur = conn.cursor()
            set_clause = ", ".join(f"{col} = %s" for col in fields)
            values = list(fields.values()) + [entry_id]
            cur.execute(f"UPDATE approval_matrix SET {set_clause} WHERE id = %s", values)
            conn.commit()
            logger.info(f"Matrix entry updated | id={entry_id} fields={list(fields)}")
        except Exception as e:
            logger.error(f"update_matrix_entry failed: {e}")
            raise


def create_matrix_entry(level: str, min_value: float, max_value: float,
                        approver_email: str, approver_name: str | None) -> None:
    with get_db() as conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO approval_matrix (level, min_value, max_value, approver_name, approver_email)
                VALUES (%s, %s, %s, %s, %s)
            """, (level, min_value, max_value, approver_name, approver_email))
            conn.commit()
            logger.info(f"Matrix entry created | level={level} email={approver_email}")
        except Exception as e:
            logger.error(f"create_matrix_entry failed: {e}")
            raise


# ── Audit Logs ────────────────────────────────────────────────

def get_audit_logs(
    limit: int = 100,
    offset: int = 0,
    action: str | None = None,
    employee_id: str | None = None,
) -> list[dict]:
    with get_db() as conn:
        try:
            cur = conn.cursor()
            query = """
                SELECT id, action, status, employee_id, entity, entity_id, detail, created_at
                FROM audit_logs
                WHERE 1=1
            """
            params: list = []
            if action:
                query += " AND action = %s"
                params.append(action)
            if employee_id:
                query += " AND employee_id = %s"
                params.append(employee_id)
            query += " ORDER BY id DESC LIMIT %s OFFSET %s"
            params += [limit, offset]
            cur.execute(query, params)
            return [
                {
                    "id":          r[0],
                    "action":      r[1],
                    "status":      r[2],
                    "employee_id": r[3],
                    "entity":      r[4],
                    "entity_id":   r[5],
                    "detail":      r[6],
                    "created_at":  str(r[7]),
                }
                for r in cur.fetchall()
            ]
        except Exception as e:
            logger.error(f"get_audit_logs failed: {e}")
            raise


# ── Products replace (CSV/Excel upload) ───────────────────────

def replace_products(rows: list[dict]) -> int:
    """Full catalog replacement: delete all old products and insert fresh rows.
    Stale plant_parts references are removed first to avoid FK violations."""
    new_parts = [row.get("part") for row in rows if row.get("part")]
    with get_db() as conn:
        try:
            cur = conn.cursor()

            if new_parts:
                placeholders = ",".join(["%s"] * len(new_parts))
                cur.execute(
                    f"DELETE FROM products WHERE part NOT IN ({placeholders})",
                    new_parts,
                )
            else:
                cur.execute("DELETE FROM products")

            count = 0
            for row in rows:
                cur.execute("""
                    INSERT INTO products (part, description, pro_type, price, is_active)
                    VALUES (%s, %s, %s, %s, TRUE)
                    ON CONFLICT (part) DO UPDATE
                        SET description = EXCLUDED.description,
                            pro_type    = EXCLUDED.pro_type,
                            price       = EXCLUDED.price,
                            is_active   = TRUE,
                            updated_at  = NOW()
                """, (
                    row.get("part"),
                    row.get("description"),
                    row.get("pro_type"),
                    row.get("price"),
                ))
                count += 1

            conn.commit()
            logger.info(f"Products replaced | inserted={count}")
            return count
        except Exception as e:
            conn.rollback()
            logger.error(f"replace_products failed: {e}")
            raise
