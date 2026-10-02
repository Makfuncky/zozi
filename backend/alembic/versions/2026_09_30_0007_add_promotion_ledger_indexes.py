"""add_promotion_ledger_indexes

Adds missing indexes on ``promotion_id`` and ``order_id`` columns of
``promotions.promotion_ledger_entries`` per ARCHITECTURE_STACK.md Law 45
(no N+1 queries, proper indexes on filtered columns) and the DB-018 finding.

Resolves:
  DB-018: promotion_id and order_id columns lack indexes, causing sequential
          scans on promotion ledger lookups by promotion or order.

Idempotent and skipped on SQLite: dev/test databases are recreated from ORM
metadata which already carries the corrected column definitions.

Revision ID: 20260930_0007
Revises: 20260930_0006
Create Date: 2026-09-30
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260930_0007"
down_revision: Union[str, None] = "20260930_0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        return

    with op.batch_alter_table("promotion_ledger_entries", schema="promotions") as batch_op:
        batch_op.create_index(
            "ix_promotions_promotion_ledger_entries_promotion_id",
            ["promotion_id"],
            if_not_exists=True,
        )
        batch_op.create_index(
            "ix_promotions_promotion_ledger_entries_order_id",
            ["order_id"],
            if_not_exists=True,
        )


def downgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        return

    with op.batch_alter_table("promotion_ledger_entries", schema="promotions") as batch_op:
        batch_op.drop_index(
            "ix_promotions_promotion_ledger_entries_promotion_id",
            if_exists=True,
        )
        batch_op.drop_index(
            "ix_promotions_promotion_ledger_entries_order_id",
            if_exists=True,
        )
