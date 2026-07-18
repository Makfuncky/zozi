"""add_staff_management_user_fields

Revision ID: s1t2u3v4w5x7
Revises: r0a1b2c3d4e5
Create Date: 2026-04-06 09:15:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = "s1t2u3v4w5x7"
down_revision: Union[str, Sequence[str], None] = "r0a1b2c3d4e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    table_names = set(inspector.get_table_names())

    if "users" not in table_names:
        return

    existing_columns = {column["name"] for column in inspector.get_columns("users")}
    columns_to_add = [
        ("full_name", sa.Column("full_name", sa.String(length=255), nullable=True)),
        ("staff_role_label", sa.Column("staff_role_label", sa.String(length=120), nullable=True)),
        ("staff_title", sa.Column("staff_title", sa.String(length=120), nullable=True)),
        ("staff_department", sa.Column("staff_department", sa.String(length=120), nullable=True)),
        (
            "staff_area_of_operation",
            sa.Column("staff_area_of_operation", sa.String(length=255), nullable=True),
        ),
        ("staff_hire_date", sa.Column("staff_hire_date", sa.Date(), nullable=True)),
        (
            "staff_experience_level",
            sa.Column("staff_experience_level", sa.String(length=120), nullable=True),
        ),
        (
            "staff_performance_summary",
            sa.Column("staff_performance_summary", sa.Text(), nullable=True),
        ),
        ("staff_assigned_tasks", sa.Column("staff_assigned_tasks", sa.JSON(), nullable=True)),
        ("staff_assigned_projects", sa.Column("staff_assigned_projects", sa.JSON(), nullable=True)),
        ("staff_permissions", sa.Column("staff_permissions", sa.JSON(), nullable=True)),
        ("staff_notes", sa.Column("staff_notes", sa.Text(), nullable=True)),
    ]

    missing_columns = [column for name, column in columns_to_add if name not in existing_columns]
    if not missing_columns:
        return

    with op.batch_alter_table("users") as batch_op:
        for column in missing_columns:
            batch_op.add_column(column)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    table_names = set(inspector.get_table_names())

    if "users" not in table_names:
        return

    existing_columns = {column["name"] for column in inspector.get_columns("users")}
    columns_to_drop = [
        "staff_notes",
        "staff_permissions",
        "staff_assigned_projects",
        "staff_assigned_tasks",
        "staff_performance_summary",
        "staff_experience_level",
        "staff_hire_date",
        "staff_area_of_operation",
        "staff_department",
        "staff_title",
        "staff_role_label",
        "full_name",
    ]
    removable_columns = [column for column in columns_to_drop if column in existing_columns]
    if not removable_columns:
        return

    with op.batch_alter_table("users") as batch_op:
        for column in removable_columns:
            batch_op.drop_column(column)
