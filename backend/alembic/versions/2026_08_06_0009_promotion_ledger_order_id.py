"""promotion_ledger_order_id

Revision ID: 20260806_0009
Revises: 20260806_0008
Create Date: 2026-08-08

Adds the ``order_id`` column to ``promotion_ledger_entries`` (commerce schema)
so per-order promotion ledger entries can be correlated back to the order that
generated the discount. Skipped on SQLite; dev/test builds from ORM.
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260806_0009"
down_revision: Union[str, None] = "20260806_0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        return

    with op.batch_alter_table("promotion_ledger_entries", schema="commerce") as batch_op:
        batch_op.add_column(sa.Column("order_id", sa.Integer(), nullable=True))
        batch_op.create_index("ix_promotion_ledger_entries_order_id", ["order_id"])


def downgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        return

    with op.batch_alter_table("promotion_ledger_entries", schema="commerce") as batch_op:
        batch_op.drop_index("ix_promotion_ledger_entries_order_id")
        batch_op.drop_column("order_id")
