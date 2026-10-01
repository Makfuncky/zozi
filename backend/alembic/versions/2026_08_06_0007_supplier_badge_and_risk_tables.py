"""supplier_badge_and_risk_tables

Revision ID: 20260806_0007
Revises: 20260806_0006
Create Date: 2026-08-06

Creates the ``employee_risk_scores`` (hr) table plus the supplier-badge tables
(``supplier_badge_catalog``, ``supplier_badges``, ``supplier_badge_billing_history``)
backing ``services.supplier.supplier_badge_service`` and ``hr_write_service``.

Skipped on SQLite: the dev/test schema is rebuilt from the ORM metadata via the
build step in ``alembic/env.py``, so the models alone drive the SQLite schema.
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260806_0007"
down_revision: Union[str, None] = "20260806_0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        return

    op.create_table(
        "employee_risk_scores",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("uuid", sa.UUID(as_uuid=True), unique=True, nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false(), index=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.Integer(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True, index=True),
        sa.Column("updated_by", sa.Integer(), nullable=True, index=True),
        sa.Column("employee_id", sa.Integer(), nullable=False, index=True),
        sa.ForeignKeyConstraint(["employee_id"], ["hr.employees.id"], ondelete="RESTRICT"),
        sa.Column("assessment_date", sa.Date(), nullable=False),
        sa.Column("score", sa.Numeric(5, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("risk_level", sa.String(20), nullable=False, server_default="low"),
        sa.Column("factors", sa.JSON(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("country_code", sa.String(10), nullable=True, index=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("employee_id", "assessment_date", name="uq_employee_risk_score"),
        sa.Index("ix_employee_risk_scores_country_created", "country_code", "created_at"),
        schema="hr",
    )

    op.create_table(
        "supplier_badge_catalog",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("uuid", sa.UUID(as_uuid=True), unique=True, nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false(), index=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.Integer(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True, index=True),
        sa.Column("updated_by", sa.Integer(), nullable=True, index=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("badge_level", sa.String(30), nullable=False, server_default="bronze"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("benefits", sa.JSON(), nullable=True),
        sa.Column("price", sa.Numeric(12, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("validity_days", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("credibility_weight", sa.Float(), nullable=False, server_default=sa.text("10")),
        sa.Column("country_code", sa.String(10), nullable=True, index=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Index("ix_supplier_badge_catalog_country_created", "country_code", "created_at"),
        schema="supplier",
    )

    op.create_table(
        "supplier_badges",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("uuid", sa.UUID(as_uuid=True), unique=True, nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false(), index=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.Integer(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True, index=True),
        sa.Column("updated_by", sa.Integer(), nullable=True, index=True),
        sa.Column("supplier_id", sa.Integer(), nullable=False, index=True),
        sa.Column("catalog_id", sa.Integer(), nullable=True, index=True),
        sa.Column("badge_name", sa.String(100), nullable=False),
        sa.Column("badge_level", sa.String(30), nullable=False, server_default="bronze"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("issued_at", sa.DateTime(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("assigned_by", sa.Integer(), nullable=True, index=True),
        sa.Column("billing_reference", sa.String(120), nullable=True),
        sa.Column("credibility_weight", sa.Float(), nullable=False, server_default=sa.text("10")),
        sa.Column("country_code", sa.String(10), nullable=True, index=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["supplier_id"], ["supplier.supplier_profiles.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["catalog_id"], ["supplier.supplier_badge_catalog.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("supplier_id", "catalog_id", name="uq_supplier_badge"),
        sa.Index("ix_supplier_badges_country_created", "country_code", "created_at"),
        schema="supplier",
    )

    op.create_table(
        "supplier_badge_billing_history",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("uuid", sa.UUID(as_uuid=True), unique=True, nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false(), index=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.Integer(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True, index=True),
        sa.Column("updated_by", sa.Integer(), nullable=True, index=True),
        sa.Column("supplier_id", sa.Integer(), nullable=False, index=True),
        sa.Column("badge_id", sa.Integer(), nullable=True, index=True),
        sa.Column("catalog_id", sa.Integer(), nullable=True, index=True),
        sa.Column("billing_reference", sa.String(120), unique=True, nullable=True),
        sa.Column("charge_type", sa.String(30), nullable=True),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("period_start", sa.DateTime(), nullable=True),
        sa.Column("period_end", sa.DateTime(), nullable=True),
        sa.Column("due_at", sa.DateTime(), nullable=True),
        sa.Column("billed_at", sa.DateTime(), nullable=True),
        sa.Column("paid_at", sa.DateTime(), nullable=True),
        sa.Column("payment_method", sa.String(30), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("country_code", sa.String(10), nullable=True, index=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["supplier_id"], ["supplier.supplier_profiles.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["badge_id"], ["supplier.supplier_badges.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["catalog_id"], ["supplier.supplier_badge_catalog.id"], ondelete="RESTRICT"),
        sa.Index("ix_supplier_badge_billing_country_created", "country_code", "created_at"),
        schema="supplier",
    )


def downgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        return
    op.drop_table("supplier_badge_billing_history", schema="supplier")
    op.drop_table("supplier_badges", schema="supplier")
    op.drop_table("supplier_badge_catalog", schema="supplier")
    op.drop_table("employee_risk_scores", schema="hr")
