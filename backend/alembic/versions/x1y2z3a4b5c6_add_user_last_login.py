"""add_user_last_login

Revision ID: x1y2z3a4b5c6
Revises: s1t2u3v4w5x7
Create Date: 2026-04-06 18:35:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = "x1y2z3a4b5c6"
down_revision: Union[str, Sequence[str], None] = "s1t2u3v4w5x7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    table_names = set(inspector.get_table_names())

    if "users" not in table_names:
        return

    existing_columns = {column["name"] for column in inspector.get_columns("users")}
    if "last_login" in existing_columns:
        return

    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("last_login", sa.DateTime(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    table_names = set(inspector.get_table_names())

    if "users" not in table_names:
        return

    existing_columns = {column["name"] for column in inspector.get_columns("users")}
    if "last_login" not in existing_columns:
        return

    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("last_login")

