import sys
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool
from sqlalchemy.engine import URL

# Make sure the project root is importable so we can load our config
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.core.config import DB_CONFIG  # noqa: E402

config = context.config

# Wire up Python logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Build the SQLAlchemy URL object directly — avoids configparser % interpolation
# issues when the password contains special characters (e.g. @, %, #).
_url = URL.create(
    drivername="postgresql+psycopg2",
    username=DB_CONFIG["user"],
    password=DB_CONFIG["password"],
    host=DB_CONFIG["host"],
    port=int(DB_CONFIG["port"]),
    database=DB_CONFIG["database"],
)

# We use raw SQL migrations (no ORM models), so target_metadata stays None.
target_metadata = None


def run_migrations_offline() -> None:
    """Run migrations without a live DB connection (produces SQL script)."""
    context.configure(
        url=_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against a live DB connection."""
    connectable = create_engine(_url, poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
