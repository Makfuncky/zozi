"""add_employee_system_tables

Admin Employees System — Phase 1: Core HR & Identity Foundation.

Creates the full employee management schema:
  - offices          Office/branch locations per country
  - employees        Employee records linked to User + Office
  - employee_documents  KYC / contract / certification files
  - employee_attendance  Daily check-in/out with geo-location
  - employee_relations  COI graph (manager, subordinate, conflict_of_interest)
  - employee_work_logs  Hours-logging with approval workflow
  - employee_roles      Role definitions per country (RBAC)

Revision ID: z1a2b3c4d5e6
Revises: p5q6r7s8t9u0
Create Date: 2026-06-24 16:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "z1a2b3c4d5e6"
down_revision: Union[str, Sequence[str], None] = "p5q6r7s8t9u0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(name: str) -> bool:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    return name in inspector.get_table_names()


def _has_column(table: str, column: str) -> bool:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    cols = {c["name"] for c in inspector.get_columns(table)}
    return column in cols


def upgrade() -> None:
    # ── offices ──────────────────────────────────────────────────────────────
    if not _has_table("offices"):
        op.create_table(
            "offices",
            sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
            sa.Column("name", sa.String(200), nullable=False),
            sa.Column("address", sa.Text(), nullable=True),
            sa.Column("city", sa.String(120), nullable=True),
            sa.Column("country_code", sa.String(10), nullable=False, index=True),
            sa.Column("phone", sa.String(60), nullable=True),
            sa.Column("email", sa.String(255), nullable=True),
            sa.Column("latitude", sa.Float(), nullable=True),
            sa.Column("longitude", sa.Float(), nullable=True),
            sa.Column("is_active", sa.Boolean(), server_default=sa.text("1"), nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_offices_country_active", "offices", ["country_code", "is_active"])

    # ── employees ────────────────────────────────────────────────────────────
    if not _has_table("employees"):
        op.create_table(
            "employees",
            sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True, index=True),
            sa.Column("employee_code", sa.String(40), nullable=True, unique=True),
            sa.Column("office_id", sa.Integer(), sa.ForeignKey("offices.id"), nullable=True, index=True),
            sa.Column("department", sa.String(120), nullable=True),
            sa.Column("position", sa.String(120), nullable=True),
            sa.Column("employment_type", sa.String(30), nullable=False, server_default=sa.text("'full_time'")),
            sa.Column("employment_status", sa.String(30), nullable=False, server_default=sa.text("'active'")),
            sa.Column("salary", sa.Numeric(12, 2), nullable=True),
            sa.Column("currency", sa.String(10), nullable=True),
            sa.Column("country_code", sa.String(10), nullable=False, index=True),
            sa.Column("is_verified", sa.Boolean(), server_default=sa.text("0"), nullable=False),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_employees_country_status", "employees", ["country_code", "employment_status"])
        op.create_index("ix_employees_user", "employees", ["user_id"])
        op.create_index("ix_employees_office", "employees", ["office_id"])

    # ── employee_documents ───────────────────────────────────────────────────
    if not _has_table("employee_documents"):
        op.create_table(
            "employee_documents",
            sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
            sa.Column("employee_id", sa.Integer(), sa.ForeignKey("employees.id"), nullable=False, index=True),
            sa.Column("document_type", sa.String(80), nullable=False),
            sa.Column("document_name", sa.String(200), nullable=False),
            sa.Column("file_url", sa.String(500), nullable=False),
            sa.Column("status", sa.String(30), nullable=False, server_default=sa.text("'pending'"), index=True),
            sa.Column("expires_at", sa.DateTime(), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("reviewed_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("reviewed_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_employee_docs_employee_type", "employee_documents", ["employee_id", "document_type"])

    # ── employee_attendance ──────────────────────────────────────────────────
    if not _has_table("employee_attendance"):
        op.create_table(
            "employee_attendance",
            sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
            sa.Column("employee_id", sa.Integer(), sa.ForeignKey("employees.id"), nullable=False, index=True),
            sa.Column("date", sa.Date(), nullable=False, index=True),
            sa.Column("check_in", sa.DateTime(), nullable=True),
            sa.Column("check_out", sa.DateTime(), nullable=True),
            sa.Column("status", sa.String(20), nullable=False, server_default=sa.text("'present'"), index=True),
            sa.Column("latitude", sa.Float(), nullable=True),
            sa.Column("longitude", sa.Float(), nullable=True),
            sa.Column("ip_address", sa.String(45), nullable=True),
            sa.Column("device_fingerprint", sa.String(64), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("employee_id", "date", name="uq_employee_attendance_date"),
        )
        op.create_index("ix_employee_attendance_status_date", "employee_attendance", ["status", "date"])

    # ── employee_relations (COI Graph) ───────────────────────────────────────
    if not _has_table("employee_relations"):
        op.create_table(
            "employee_relations",
            sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
            sa.Column("employee_id", sa.Integer(), sa.ForeignKey("employees.id"), nullable=False, index=True),
            sa.Column("related_employee_id", sa.Integer(), sa.ForeignKey("employees.id"), nullable=False, index=True),
            sa.Column("relation_type", sa.String(40), nullable=False, index=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("is_active", sa.Boolean(), server_default=sa.text("1"), nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("employee_id", "related_employee_id", "relation_type", name="uq_employee_relation"),
        )
        op.create_index("ix_employee_relations_type_active", "employee_relations", ["relation_type", "is_active"])

    # ── employee_work_logs ───────────────────────────────────────────────────
    if not _has_table("employee_work_logs"):
        op.create_table(
            "employee_work_logs",
            sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
            sa.Column("employee_id", sa.Integer(), sa.ForeignKey("employees.id"), nullable=False, index=True),
            sa.Column("date", sa.Date(), nullable=False, index=True),
            sa.Column("hours_worked", sa.Float(), nullable=False, server_default=sa.text("0")),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("status", sa.String(20), nullable=False, server_default=sa.text("'pending'"), index=True),
            sa.Column("approved_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("approved_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_employee_work_logs_employee_date", "employee_work_logs", ["employee_id", "date"])
        op.create_index("ix_employee_work_logs_status_date", "employee_work_logs", ["status", "date"])

    # ── employee_roles ───────────────────────────────────────────────────────
    if not _has_table("employee_roles"):
        op.create_table(
            "employee_roles",
            sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
            sa.Column("name", sa.String(120), nullable=False),
            sa.Column("slug", sa.String(120), nullable=False),
            sa.Column("country_code", sa.String(10), nullable=False, index=True),
            sa.Column("permissions", sa.JSON(), nullable=True),
            sa.Column("is_active", sa.Boolean(), server_default=sa.text("1"), nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("slug", "country_code", name="uq_employee_role_slug_country"),
        )
        op.create_index("ix_employee_roles_country_active", "employee_roles", ["country_code", "is_active"])


def downgrade() -> None:
    op.drop_table("employee_work_logs")
    op.drop_table("employee_relations")
    op.drop_table("employee_attendance")
    op.drop_table("employee_documents")
    op.drop_table("employee_roles")
    op.drop_table("employees")
    op.drop_table("offices")

