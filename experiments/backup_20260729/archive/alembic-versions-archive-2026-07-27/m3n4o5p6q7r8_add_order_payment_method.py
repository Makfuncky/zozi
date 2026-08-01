"""add_order_payment_method

Revision ID: m3n4o5p6q7r8
Revises: k2l3m4n5o6p7
Create Date: 2026-03-27 21:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = "m3n4o5p6q7r8"
down_revision: Union[str, Sequence[str], None] = "k2l3m4n5o6p7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "orders" not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns("orders")}
    if "payment_method" in existing_columns:
        return

    with op.batch_alter_table("orders", schema=None) as batch_op:
        batch_op.add_column(sa.Column("payment_method", sa.String(length=20), nullable=False, server_default="card"))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "orders" not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns("orders")}
    if "payment_method" not in existing_columns:
        return

    with op.batch_alter_table("orders", schema=None) as batch_op:
        batch_op.drop_column("payment_method")

