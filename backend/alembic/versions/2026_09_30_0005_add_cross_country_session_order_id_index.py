"""add_cross_country_session_order_id_index

Adds missing index on ``order_id`` column of
``customers.cross_country_customer_sessions`` per ARCHITECTURE_STACK.md
Law 53 (all FK columns must have explicit indexes because PostgreSQL does
NOT auto-index FKs).

Resolves:
  DB-005: ``order_id`` at line 39 of
          ``backend/domains/customers/models/cross_country_session.py``
          lacks ``index=True``, causing sequential scans on order lookups.

Idempotent and skipped on SQLite: dev/test databases are recreated from
ORM metadata which already carries the corrected column definition.

Revision ID: 20260930_0005
Revises: 20260930_0004
Create Date: 2026-09-30
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260930_0005"
down_revision: Union[str, None] = "20260930_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        return

    with op.batch_alter_table("cross_country_customer_sessions", schema="customers") as batch_op:
        batch_op.create_index(
            "ix_customers_cross_country_customer_sessions_order_id",
            ["order_id"],
            if_not_exists=True,
        )


def downgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        return

    with op.batch_alter_table("cross_country_customer_sessions", schema="customers") as batch_op:
        batch_op.drop_index(
            "ix_customers_cross_country_customer_sessions_order_id",
            if_exists=True,
        )
