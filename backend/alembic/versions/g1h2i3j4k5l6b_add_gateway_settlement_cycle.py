"""add_gateway_settlement_cycle

Revision ID: q1r2s3t4u5v6
Revises: 05a62fd3c5d3
Create Date: 2026-04-05 19:35:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = "g1h2i3j4k5l6b"
down_revision: Union[str, Sequence[str], None] = "05a62fd3c5d3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("payment_gateway_connections")}

    if "settlement_cycle" not in columns:
        op.add_column(
            "payment_gateway_connections",
            sa.Column("settlement_cycle", sa.String(length=20), nullable=False, server_default="weekly"),
        )

    op.execute("UPDATE payment_gateway_connections SET settlement_cycle = COALESCE(settlement_cycle, 'weekly')")


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("payment_gateway_connections")}

    if "settlement_cycle" in columns:
        with op.batch_alter_table("payment_gateway_connections") as batch_op:
            batch_op.drop_column("settlement_cycle")

