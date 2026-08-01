"""Add hierarchy columns — materialized path/depth on org_units, notes on employee_relations.

Revision ID: ems_hierarchy_columns_20260726
Revises: ems_gap_tables_20260725
Create Date: 2026-07-26
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "ems_hierarchy_columns_20260726"
down_revision = "ems_gap_tables_20260725"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── OrgUnits: materialized path + depth ──────────────────────
    op.add_column("org_units", sa.Column("path", sa.String(500), nullable=True))
    op.add_column("org_units", sa.Column("depth", sa.Integer(), default=0))
    op.create_index("ix_org_unit_path", "org_units", ["path"])
    op.create_index("ix_org_unit_parent", "org_units", ["parent_id"])

    # ── EmployeeRelations: notes column + indexes ────────────────
    op.add_column("employee_relations", sa.Column("notes", sa.Text(), nullable=True))
    op.create_index("ix_emp_rel_type", "employee_relations", ["relation_type"])
    op.create_index("ix_emp_rel_internal", "employee_relations", ["internal_employee_id"])


def downgrade() -> None:
    op.drop_index("ix_emp_rel_internal", table_name="employee_relations")
    op.drop_index("ix_emp_rel_type", table_name="employee_relations")
    op.drop_column("employee_relations", "notes")
    op.drop_index("ix_org_unit_parent", table_name="org_units")
    op.drop_index("ix_org_unit_path", table_name="org_units")
    op.drop_column("org_units", "depth")
    op.drop_column("org_units", "path")
