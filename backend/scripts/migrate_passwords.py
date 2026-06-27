"""
One-time migration: hash all plain-text passwords in the users table using bcrypt.

Run once after deploying Phase 5 (password hashing):

    uv run python -m backend.scripts.migrate_passwords

Safe to run multiple times — already-hashed passwords (starting with $2b$) are skipped.
"""

from backend.database.connection import get_connection
from backend.core.security import hash_password
from backend.core.logger import get_logger

logger = get_logger("migrate_passwords")


def migrate():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT employee_id, password FROM users")
        users = cur.fetchall()

        migrated = 0
        skipped = 0

        for employee_id, password in users:
            if password.startswith("$2b$"):
                skipped += 1
                continue

            hashed = hash_password(password)
            cur.execute(
                "UPDATE users SET password = %s WHERE employee_id = %s",
                (hashed, employee_id),
            )
            migrated += 1
            logger.info(f"Hashed password for employee: {employee_id}")

        conn.commit()
        logger.info(f"Migration complete — migrated={migrated} skipped={skipped}")
        print(f"Done. Migrated: {migrated}  |  Already hashed (skipped): {skipped}")

    except Exception as e:
        conn.rollback()
        logger.error(f"Migration failed: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
