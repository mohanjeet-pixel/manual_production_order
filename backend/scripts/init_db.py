"""Database bootstrap — create the database (if missing) and apply migrations.

Idempotent: safe to run on every startup. It will
  1. connect to the PostgreSQL maintenance database and `CREATE DATABASE`
     the target DB if it does not already exist, then
  2. run all Alembic migrations up to `head` (which use
     `CREATE TABLE / COLUMN IF NOT EXISTS`, so existing data is preserved).

Run manually:
    uv run python -m backend.scripts.init_db
"""

from pathlib import Path

import psycopg2
from psycopg2 import sql
from alembic import command
from alembic.config import Config

from backend.core.config import DB_CONFIG
from backend.core.logger import get_logger

logger = get_logger("init_db")

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_ALEMBIC_INI = _PROJECT_ROOT / "alembic.ini"


def ensure_database() -> bool:
    """Create the target database if it doesn't exist. Returns True if created."""
    target = DB_CONFIG["database"]
    # Connect to the maintenance DB (not the target) to be able to CREATE it.
    admin_cfg = {**DB_CONFIG, "database": "postgres"}

    conn = psycopg2.connect(**admin_cfg)
    try:
        conn.autocommit = True  # CREATE DATABASE can't run inside a transaction
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (target,))
            if cur.fetchone():
                logger.info(f"Database '{target}' already exists")
                return False
            cur.execute(
                sql.SQL("CREATE DATABASE {}").format(sql.Identifier(target))
            )
            logger.info(f"Created database '{target}'")
            return True
    finally:
        conn.close()


def run_migrations() -> None:
    """Apply all Alembic migrations up to head."""
    cfg = Config(str(_ALEMBIC_INI))
    cfg.set_main_option("script_location", str(_PROJECT_ROOT / "alembic"))
    logger.info("Applying database migrations (alembic upgrade head)...")
    command.upgrade(cfg, "head")
    logger.info("Database schema is up to date")


def ensure_schema() -> None:
    """Full bootstrap: database + tables + columns + seed data."""
    ensure_database()
    run_migrations()


if __name__ == "__main__":
    ensure_schema()
    print("Database is ready.")
