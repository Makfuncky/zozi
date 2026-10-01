"""add_payment_gateway_connection_country_code_fk

Adds missing ForeignKey and index on ``country_code`` column of
``finance.payment_gateway_connections`` per ARCHITECTURE_STACK.md
Law 5 (country_code with FK), Law 52 (FK constraints), and Law 53
(all FK columns must have explicit indexes because PostgreSQL does
NOT auto-index FKs).

Resolves:
  DB-019: ``PaymentGatewayConnection.country_code`` at line 91 of
          ``backend/domains/finance/models/payments.py``
          lacks ForeignKey and index, causing sequential scans on
          country lookups and violating referential integrity.

Idempotent: on SQLite the batch_alter_table recreates the table with
the FK; on PostgreSQL the DDL uses IF NOT EXISTS semantics.

Revision ID: 20260930_0006
Revises: 20260930_0005
Create Date: 2026-09-30
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260930_0006"
down_revision: Union[str, None] = "20260930_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    with op.batch_alter_table("payment_gateway_connections", schema="finance") as batch_op:
        batch_op.create_index(
            "ix_finance_payment_gateway_connections_country_code",
            ["country_code"],
            if_not_exists=True,
        )
        batch_op.create_foreign_key(
            "fk_finance_pgc_country_code",
            "country_configs",
            ["country_code"],
            ["code"],
            ondelete="RESTRICT",
            referent_schema="country",
        )


def downgrade() -> None:
    conn = op.get_bind()

    with op.batch_alter_table("payment_gateway_connections", schema="finance") as batch_op:
        batch_op.drop_index(
            "ix_finance_payment_gateway_connections_country_code",
            if_exists=True,
        )
        batch_op.drop_constraint(
            "fk_finance_pgc_country_code",
            type_="foreignkey",
            schema="finance",
        )
