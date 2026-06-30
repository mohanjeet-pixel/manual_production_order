"""Drop plants and plant_parts tables

These tables are unused — no application code queries them (the products
catalog plus the products.plant column carry the plant/part data). Remove them.

Revision ID: 0005
Revises: 0004
Create Date: 2026-06-30
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # plant_parts first — it has an FK to plants
    op.execute("DROP TABLE IF EXISTS plant_parts")
    op.execute("DROP TABLE IF EXISTS plants")


def downgrade() -> None:
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
