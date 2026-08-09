"""add_order_gateway_fee_fields

Revision ID: f8a9b0c1d2e3
Revises: e7f8a9b0c1d2
Create Date: 2026-04-05 18:20:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = "f8a9b0c1d2e3"
down_revision: Union[str, Sequence[str], None] = "e7f8a9b0c1d2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _index_names(inspector: sa.Inspector, table_name: str) -> set[str]:
    return {index["name"] for index in inspector.get_indexes(table_name)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("orders")}
    indexes = _index_names(inspector, "orders")

    if "payment_gateway_code" not in columns:
        op.add_column("orders", sa.Column("payment_gateway_code", sa.String(length=60), nullable=True))
    if "ix_orders_payment_gateway_code" not in indexes:
        op.create_index("ix_orders_payment_gateway_code", "orders", ["payment_gateway_code"], unique=False)
    if "payment_gateway_fee_amount" not in columns:
        op.add_column(
            "orders",
            sa.Column("payment_gateway_fee_amount", sa.Numeric(12, 2), nullable=True, server_default="0"),
        )
    if "payment_customer_total_amount" not in columns:
        op.add_column("orders", sa.Column("payment_customer_total_amount", sa.Numeric(12, 2), nullable=True))
    if "payment_gateway_fee_passed_to_customer" not in columns:
        op.add_column(
            "orders",
            sa.Column(
                "payment_gateway_fee_passed_to_customer",
                sa.Boolean(),
                nullable=True,
                server_default=sa.false(),
            ),
        )

    op.execute("UPDATE orders SET payment_gateway_fee_amount = COALESCE(payment_gateway_fee_amount, 0)")
    op.execute("UPDATE orders SET payment_customer_total_amount = COALESCE(payment_customer_total_amount, total_amount)")
    op.execute("UPDATE orders SET payment_gateway_fee_passed_to_customer = COALESCE(payment_gateway_fee_passed_to_customer, FALSE)")


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("orders")}
    indexes = _index_names(inspector, "orders")

    with op.batch_alter_table("orders") as batch_op:
        if batch_op.f("ix_orders_payment_gateway_code") in indexes:
            batch_op.drop_index(batch_op.f("ix_orders_payment_gateway_code"))
        if "payment_gateway_fee_passed_to_customer" in columns:
            batch_op.drop_column("payment_gateway_fee_passed_to_customer")
        if "payment_customer_total_amount" in columns:
            batch_op.drop_column("payment_customer_total_amount")
        if "payment_gateway_fee_amount" in columns:
            batch_op.drop_column("payment_gateway_fee_amount")
        if "payment_gateway_code" in columns:
            batch_op.drop_column("payment_gateway_code")

