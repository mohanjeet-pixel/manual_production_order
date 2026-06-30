"""Rename products.pro_type → products.plant

The column has always stored the Plant code (e.g. 1000 / 1500) from the
Excel upload. Rename it to `plant` so the column name matches its meaning.

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-30
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE products RENAME COLUMN pro_type TO plant")
    op.execute("COMMENT ON COLUMN products.plant IS 'Plant code from upload: 1000 or 1500'")


def downgrade() -> None:
    op.execute("ALTER TABLE products RENAME COLUMN plant TO pro_type")
    op.execute("COMMENT ON COLUMN products.pro_type IS 'Plant code from upload: 1000 or 1500'")
