"""add_role_permission_settings

Revision ID: r0a1b2c3d4e5
Revises: p9q8r7s6t5u4
Create Date: 2026-04-05 21:10:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = "r0a1b2c3d4e5"
down_revision: Union[str, Sequence[str], None] = "p9q8r7s6t5u4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    table_names = set(inspector.get_table_names())

    if "role_permission_settings" not in table_names:
        op.create_table(
            "role_permission_settings",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("role", sa.String(length=50), nullable=False),
            sa.Column("permissions", sa.JSON(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.Column("updated_by_id", sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"]),
            sa.UniqueConstraint("role", name="uq_role_permission_settings_role"),
        )
        op.create_index("ix_role_permission_settings_role", "role_permission_settings", ["role"], unique=False)
        return

    columns = {column["name"] for column in inspector.get_columns("role_permission_settings")}
    indexes = {index["name"] for index in inspector.get_indexes("role_permission_settings")}

    if "updated_by_id" not in columns:
        with op.batch_alter_table("role_permission_settings") as batch_op:
            batch_op.add_column(sa.Column("updated_by_id", sa.Integer(), nullable=True))
            batch_op.create_foreign_key(
                "fk_role_permission_settings_updated_by_id_users",
                "users",
                ["updated_by_id"],
                ["id"],
            )

    if "ix_role_permission_settings_role" not in indexes:
        op.create_index("ix_role_permission_settings_role", "role_permission_settings", ["role"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    table_names = set(inspector.get_table_names())

    if "role_permission_settings" in table_names:
        indexes = {index["name"] for index in inspector.get_indexes("role_permission_settings")}
        if "ix_role_permission_settings_role" in indexes:
            op.drop_index("ix_role_permission_settings_role", table_name="role_permission_settings")
        op.drop_table("role_permission_settings")

