"""phase1_employee_hierarchy

Adds employee hierarchy authority and org-unit scaffolding:
  - authority_level / org_unit_id columns on employees
  - org_units table
  - authority_level / approval flag columns on employee_roles

Revision ID: p1h2i3j4k5l6
Revises: zd1e2f3a4b5c
Create Date: 2026-07-02 02:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "p1h2i3j4k5l6"
down_revision: Union[str, Sequence[str], None] = "zd1e2f3a4b5c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "org_units" not in inspector.get_table_names():
        op.create_table(
            "org_units",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=200), nullable=False),
            sa.Column("parent_id", sa.Integer(), nullable=True),
            sa.Column("country_code", sa.String(length=10), nullable=True),
            sa.Column("level", sa.Integer(), server_default="1", nullable=False),
            sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(["parent_id"], ["org_units.id"], ondelete="SET NULL"),
        )

    if not any(
        col["name"] == "authority_level"
        for col in inspector.get_columns("employees")
    ):
        op.add_column("employees", sa.Column("authority_level", sa.Integer(), nullable=True))

    if not any(
        col["name"] == "org_unit_id"
        for col in inspector.get_columns("employees")
    ):
        op.add_column(
            "employees",
            sa.Column("org_unit_id", sa.Integer(), nullable=True),
        )
        op.create_index("ix_employees_org_unit_id", "employees", ["org_unit_id"])
        op.create_foreign_key(
            "fk_employees_org_unit_id",
            "employees",
            "org_units",
            ["org_unit_id"],
            ["id"],
            ondelete="SET NULL",
        )

    if not any(
        col["name"] == "authority_level"
        for col in inspector.get_columns("employee_roles")
    ):
        op.add_column(
            "employee_roles",
            sa.Column("authority_level", sa.Integer(), nullable=True),
        )

    if not any(
        col["name"] == "can_approve_leave"
        for col in inspector.get_columns("employee_roles")
    ):
        op.add_column(
            "employee_roles",
            sa.Column("can_approve_leave", sa.Boolean(), server_default=sa.false(), nullable=False),
        )

    if not any(
        col["name"] == "can_approve_expense"
        for col in inspector.get_columns("employee_roles")
    ):
        op.add_column(
            "employee_roles",
            sa.Column("can_approve_expense", sa.Boolean(), server_default=sa.false(), nullable=False),
        )

    if not any(
        col["name"] == "can_manage_users"
        for col in inspector.get_columns("employee_roles")
    ):
        op.add_column(
            "employee_roles",
            sa.Column("can_manage_users", sa.Boolean(), server_default=sa.false(), nullable=False),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    for column in ("can_manage_users", "can_approve_expense", "can_approve_leave", "authority_level"):
        if any(col["name"] == column for col in inspector.get_columns("employee_roles")):
            op.drop_column("employee_roles", column)

    if any(col["name"] == "org_unit_id" for col in inspector.get_columns("employees")):
        op.drop_constraint("fk_employees_org_unit_id", "employees", type_="foreignkey")
        op.drop_index("ix_employees_org_unit_id", table_name="employees")
        op.drop_column("employees", "org_unit_id")

    if any(col["name"] == "authority_level" for col in inspector.get_columns("employees")):
        op.drop_column("employees", "authority_level")

    if "org_units" in inspector.get_table_names():
        op.drop_table("org_units")

