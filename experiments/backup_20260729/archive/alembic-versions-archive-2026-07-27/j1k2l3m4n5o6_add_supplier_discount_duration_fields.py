"""add_supplier_discount_duration_fields

Revision ID: j1k2l3m4n5o6
Revises: d5477adebb01, h7i8j9k0l1m2
Create Date: 2026-03-26 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = "j1k2l3m4n5o6"
down_revision: Union[str, Sequence[str], None] = ("d5477adebb01", "h7i8j9k0l1m2")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("products")}

    with op.batch_alter_table("products", schema=None) as batch_op:
        if "discount_starts_at" not in columns:
            batch_op.add_column(sa.Column("discount_starts_at", sa.DateTime(), nullable=True))
        if "discount_ends_at" not in columns:
            batch_op.add_column(sa.Column("discount_ends_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("products")}

    with op.batch_alter_table("products", schema=None) as batch_op:
        if "discount_ends_at" in columns:
            batch_op.drop_column("discount_ends_at")
        if "discount_starts_at" in columns:
            batch_op.drop_column("discount_starts_at")

