"""Add remark column to orders and batches

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-30
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE manual_production_orders
        ADD COLUMN IF NOT EXISTS remark TEXT
    """)
    op.execute("""
        ALTER TABLE manual_order_batches
        ADD COLUMN IF NOT EXISTS remark TEXT
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE manual_production_orders DROP COLUMN IF EXISTS remark")
    op.execute("ALTER TABLE manual_order_batches    DROP COLUMN IF EXISTS remark")
