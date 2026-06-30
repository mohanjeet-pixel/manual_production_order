"""Add plants and plant_parts tables

These tables back the admin plant/part management screens (see
backend/repositories/admin_repository.py). They existed on live databases but
were missing from the migrations, so a freshly created database lacked them.
Created with IF NOT EXISTS so existing databases are left untouched.

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-30
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS plants (
            plant_id    VARCHAR(20)  PRIMARY KEY,
            plant_name  VARCHAR(100) NOT NULL,
            location    VARCHAR(200),
            is_active   BOOLEAN      NOT NULL DEFAULT TRUE,
            created_at  TIMESTAMP    NOT NULL DEFAULT NOW()
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS plant_parts (
            id          SERIAL        PRIMARY KEY,
            plant_id    VARCHAR(20)   NOT NULL
                                      REFERENCES plants(plant_id) ON DELETE CASCADE,
            part_no     VARCHAR(50)   NOT NULL,
            unit_price  NUMERIC(14,2),
            is_active   BOOLEAN       NOT NULL DEFAULT TRUE,
            created_at  TIMESTAMP     NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_plant_part UNIQUE (plant_id, part_no)
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_plant_parts_plant ON plant_parts (plant_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_plant_parts_part  ON plant_parts (part_no)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS plant_parts")
    op.execute("DROP TABLE IF EXISTS plants")
