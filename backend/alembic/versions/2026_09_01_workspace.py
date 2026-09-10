"""Add employee workspace, task, role, and notification tables

Revision ID: 20260901_workspace
Revises: 20260827_audit_logs_worm_hash
Create Date: 2026-09-01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


revision: str = "20260901_workspace"
down_revision: Union[str, None] = "20260827_audit_logs_worm_hash"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    
    # ── Role Definitions ────────────────────────────────────────────────
    op.create_table(
        "role_definitions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("role_id", sa.String(50), unique=True, nullable=False, index=True),
        sa.Column("role_name", sa.String(100), nullable=False),
        sa.Column("department", sa.String(50), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("icon", sa.String(50), nullable=True),
        sa.Column("color", sa.String(20), nullable=True),
        sa.Column("default_features", sa.JSON(), server_default="[]"),
        sa.Column("default_widgets", sa.JSON(), server_default="[]"),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False, index=True),
        sa.Column("country_code", sa.String(2), nullable=True, index=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        schema="hr",
    )

    # ── Employee Role Assignments ───────────────────────────────────────
    op.create_table(
        "employee_role_assignments",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("employee_id", sa.Integer(), sa.ForeignKey("hr.employees.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(50), nullable=False, index=True),
        sa.Column("department", sa.String(50), nullable=True),
        sa.Column("team_id", sa.Integer(), sa.ForeignKey("hr.org_units.id", ondelete="SET NULL"), nullable=True),
        sa.Column("is_primary", sa.Boolean(), server_default="false"),
        sa.Column("assigned_by", sa.Integer(), sa.ForeignKey("hr.employees.id", ondelete="SET NULL"), nullable=False),
        sa.Column("assigned_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("country_code", sa.String(2), nullable=True, index=True),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint("employee_id", "role", name="uq_employee_role"),
        schema="hr",
    )

    # ── Employee Tasks ──────────────────────────────────────────────────
    op.create_table(
        "employee_tasks",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("task_type", sa.String(50), nullable=False),
        sa.Column("assigned_to_id", sa.Integer(), sa.ForeignKey("hr.employees.id", ondelete="CASCADE"), nullable=False),
        sa.Column("assigned_by_id", sa.Integer(), sa.ForeignKey("hr.employees.id", ondelete="SET NULL"), nullable=False),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("priority", sa.String(20), server_default="medium"),
        sa.Column("due_date", sa.DateTime(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("entity_type", sa.String(50), nullable=True),
        sa.Column("entity_id", sa.Integer(), nullable=True),
        sa.Column("entity_url", sa.String(500), nullable=True),
        sa.Column("notes", sa.JSON(), server_default="[]"),
        sa.Column("attachments", sa.JSON(), server_default="[]"),
        sa.Column("country_code", sa.String(2), nullable=True, index=True),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.CheckConstraint("status IN ('pending', 'in_progress', 'completed', 'blocked', 'cancelled')", name="chk_employee_tasks_status_valid"),
        sa.CheckConstraint("priority IN ('high', 'medium', 'low')", name="chk_employee_tasks_priority_valid"),
        schema="hr",
    )

    # ── Employee Task Comments ──────────────────────────────────────────
    op.create_table(
        "employee_task_comments",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("task_id", sa.Integer(), sa.ForeignKey("hr.employee_tasks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("employee_id", sa.Integer(), sa.ForeignKey("hr.employees.id", ondelete="CASCADE"), nullable=False),
        sa.Column("comment", sa.Text(), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        schema="hr",
    )

    # ── Employee Workspace Config ───────────────────────────────────────
    op.create_table(
        "employee_workspace_configs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("employee_id", sa.Integer(), sa.ForeignKey("hr.employees.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(50), nullable=False),
        sa.Column("enabled_features", sa.JSON(), server_default="[]"),
        sa.Column("dashboard_widgets", sa.JSON(), server_default="[]"),
        sa.Column("layout_config", sa.JSON(), server_default="{}"),
        sa.Column("country_code", sa.String(2), nullable=True, index=True),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint("employee_id", "role", name="uq_employee_workspace"),
        schema="hr",
    )

    # ── Employee Notifications ──────────────────────────────────────────
    op.create_table(
        "employee_notifications",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("employee_id", sa.Integer(), sa.ForeignKey("hr.employees.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("is_read", sa.Boolean(), server_default="false"),
        sa.Column("action_url", sa.String(500), nullable=True),
        sa.Column("entity_type", sa.String(50), nullable=True),
        sa.Column("entity_id", sa.Integer(), nullable=True),
        sa.Column("country_code", sa.String(2), nullable=True, index=True),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        schema="comms",
    )

    # ── Seed Role Definitions ───────────────────────────────────────────
    if conn.dialect.name == "sqlite" or conn.dialect.name == "postgresql":
        roles = [
            ("moderator", "Content Moderator", "Content", "Moderate reviews, product descriptions, user content"),
            ("supplier_coordinator", "Supplier Coordinator", "Procurement", "Manage supplier relationships, orders, issues"),
            ("customer_coordinator", "Customer Coordinator", "Support", "Handle customer tickets, returns, escalations"),
            ("promotion_manager", "Promotion Manager", "Marketing", "Create/manage campaigns, deals, banners"),
            ("order_fulfillment", "Order Fulfillment", "Warehouse", "Process orders, manage inventory, shipping"),
            ("delivery_coordinator", "Delivery Coordinator", "Logistics", "Manage drivers, routes, tracking"),
            ("finance_clerk", "Finance Clerk", "Finance", "Process invoices, payments, reconciliation"),
            ("hr_coordinator", "HR Coordinator", "HR", "Assist with employee records, onboarding"),
            ("data_entry", "Data Entry", "Operations", "Enter/update product data, catalog management"),
            ("quality_analyst", "Quality Analyst", "Quality", "Check product quality, handle complaints"),
            ("social_media", "Social Media Manager", "Marketing", "Manage social posts, engagement"),
            ("inventory_manager", "Inventory Manager", "Warehouse", "Track stock, manage warehouses, reorder"),
            ("returns_processor", "Returns Processor", "Support", "Process returns, refunds, exchanges"),
            ("content_writer", "Content Writer", "Content", "Write product descriptions, blog posts"),
            ("photography_editor", "Photography Editor", "Media", "Edit product images, manage media library"),
            ("accounts_payable", "Accounts Payable", "Finance", "Process supplier invoices, payments"),
            ("accounts_receivable", "Accounts Receivable", "Finance", "Track customer payments, follow-ups"),
        ]
        
        for role_id, role_name, department, description in roles:
            op.execute(
                text(
                    "INSERT INTO hr.role_definitions (role_id, role_name, department, description, is_active) "
                    "VALUES (:role_id, :role_name, :department, :description, true)"
                ),
                {"role_id": role_id, "role_name": role_name, "department": department, "description": description},
            )


def downgrade() -> None:
    op.drop_table("employee_notifications", schema="comms")
    op.drop_table("employee_workspace_configs", schema="hr")
    op.drop_table("employee_task_comments", schema="hr")
    op.drop_table("employee_tasks", schema="hr")
    op.drop_table("employee_role_assignments", schema="hr")
    op.drop_table("role_definitions", schema="hr")
