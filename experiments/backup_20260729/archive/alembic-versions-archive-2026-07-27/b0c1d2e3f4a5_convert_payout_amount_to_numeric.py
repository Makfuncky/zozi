"""convert_payout_amount_to_numeric

Convert Payout.amount and LogisticsPartnerPayout.amount from Float to
Numeric(12, 2) to avoid floating-point precision issues in financial data.

Revision ID: b0c1d2e3f4a5
Revises: a9b0c1d2e3f4
Create Date: 2026-04-01 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = "b0c1d2e3f4a5"
down_revision: Union[str, Sequence[str], None] = "a9b0c1d2e3f4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = inspector.get_table_names()

    if "payouts" in tables:
        with op.batch_alter_table("payouts") as batch_op:
            batch_op.alter_column(
                "amount",
                existing_type=sa.Float(),
                type_=sa.Numeric(12, 2),
                existing_nullable=False,
            )

    if "logistics_partner_payouts" in tables:
        with op.batch_alter_table("logistics_partner_payouts") as batch_op:
            batch_op.alter_column(
                "amount",
                existing_type=sa.Float(),
                type_=sa.Numeric(12, 2),
                existing_nullable=False,
            )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = inspector.get_table_names()

    if "logistics_partner_payouts" in tables:
        with op.batch_alter_table("logistics_partner_payouts") as batch_op:
            batch_op.alter_column(
                "amount",
                existing_type=sa.Numeric(12, 2),
                type_=sa.Float(),
                existing_nullable=False,
            )

    if "payouts" in tables:
        with op.batch_alter_table("payouts") as batch_op:
            batch_op.alter_column(
                "amount",
                existing_type=sa.Numeric(12, 2),
                type_=sa.Float(),
                existing_nullable=False,
            )

