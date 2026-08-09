"""role_permission_setting_maker_checker

Revision ID: 20260806_0008
Revises: 20260806_0007
Create Date: 2026-08-08

Adds maker-checker columns to ``role_permission_settings`` (security schema):
``pending_permissions_json`` (the staged set) and ``is_approved`` (whether the
active set has been approved). Skipped on SQLite; dev/test builds from ORM.
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260806_0008"
down_revision: Union[str, None] = "20260806_0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        return

    with op.batch_alter_table("role_permission_settings", schema="security") as batch_op:
        batch_op.add_column(sa.Column("pending_permissions_json", sa.JSON(), nullable=True))
        batch_op.add_column(
            sa.Column("is_approved", sa.Boolean(), nullable=False, server_default=sa.true())
        )


def downgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        return

    with op.batch_alter_table("role_permission_settings", schema="security") as batch_op:
        batch_op.drop_column("is_approved")
        batch_op.drop_column("pending_permissions_json")
