"""Add composite indexes for hot query paths

Revision ID: 20260831_0004
Revises: 20260831_0003
Create Date: 2026-08-31
"""
import sqlalchemy as sa
from typing import Sequence, Union

from alembic import op
from sqlalchemy.sql import quoted_name as sql_identifier

revision: str = "20260831_0004"
down_revision: Union[str, None] = "20260831_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Composite indexes for hot query paths (from document §7.1)
COMPOSITE_INDEXES = [
    # Commerce - products (hot list queries)
    ("commerce", "products", "ix_products_country_created", ["country_code", "created_at"]),
    ("commerce", "products", "ix_products_country_status", ["country_code", "moderation_status"]),
    ("commerce", "products", "ix_products_country_featured", ["country_code", "is_featured", "is_active"]),
    ("commerce", "products", "ix_products_supplier_active", ["supplier_id", "is_active"]),
    ("commerce", "products", "ix_products_category_active", ["category_id", "is_active"]),
    # Commerce - orders (hot list queries)
    ("commerce", "orders", "ix_orders_country_status", ["country_code", "status_code"]),
    ("commerce", "orders", "ix_orders_user_country", ["user_id", "country_code"]),
    ("commerce", "orders", "ix_orders_country_created", ["country_code", "created_at"]),
    # Customer
    ("customer", "customers", "ix_customers_country_active", ["country_code", "is_active"]),
    ("customer", "addresses", "ix_addresses_user_country", ["user_id", "country_code"]),
    # Supplier
    ("supplier", "supplier_profiles", "ix_supplier_country_status", ["country_code", "verification_status"]),
    # Logistics
    ("logistics", "logistics_partners", "ix_logistics_country_status", ["country_code", "status_code"]),
    ("logistics", "shipments", "ix_shipments_country_status", ["country_code", "status_code"]),
    # Finance
    ("finance", "journal_entries", "ix_journal_country_created", ["country_code", "created_at"]),
    ("finance", "accounts", "ix_accounts_country_type", ["country_code", "account_type"]),
    # Treasury
    ("treasury", "treasury_accounts", "ix_treasury_country_type", ["country_code", "account_type"]),
    # HR
    ("hr", "employees", "ix_employees_country_status", ["country_code", "employment_status"]),
    ("hr", "employee_attendance", "ix_attendance_employee_date", ["employee_id", "attendance_date"]),
    # Communication
    ("comms", "notifications", "ix_notifications_user_read", ["user_id", "is_read"]),
    ("comms", "notifications", "ix_notifications_country_created", ["country_code", "created_at"]),
    # Security
    ("security", "fraud_alerts", "ix_fraud_country_status", ["country_code", "status_code"]),
    ("security", "ip_reputations", "ix_ip_reputation_score", ["ip_address", "reputation_score"]),
    # Audit
    ("audit", "audit_logs", "ix_audit_country_action", ["country_code", "action"]),
    ("audit", "audit_logs", "ix_audit_entity", ["entity_type", "entity_id"]),
    # Country
    ("country", "country_configs", "ix_country_active", ["is_active", "is_default"]),
]

# Partial indexes for hot subsets (from document §7.1)
PARTIAL_INDEXES = [
    # Active products only
    ("commerce", "products", "ix_products_active_country", ["country_code", "id"], "is_active = true AND is_deleted = false"),
    # Active orders only
    ("commerce", "orders", "ix_orders_active_country", ["country_code", "created_at"], "is_deleted = false"),
    # Active users only
    ("core", "users", "ix_users_active_country", ["country_code", "id"], "is_active = true AND is_deleted = false"),
    # Unread notifications only
    ("comms", "notifications", "ix_notifications_unread", ["user_id", "created_at"], "is_read = false AND is_deleted = false"),
]


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        return  # SQLite indexes are less critical, skip for dev

    # Create composite indexes
    for schema, table, idx_name, columns in COMPOSITE_INDEXES:
        col_list = ", ".join(columns)
        sch = sql_identifier(schema)
        tbl = sql_identifier(table)
        idx = sql_identifier(idx_name)
        op.execute(
            sa.text('CREATE INDEX IF NOT EXISTS :idx ON :sch.:tbl (:cols)'),
            {"idx": idx, "sch": sch, "tbl": tbl, "cols": col_list},
        )

    # Create partial indexes
    for schema, table, idx_name, columns, where_clause in PARTIAL_INDEXES:
        col_list = ", ".join(columns)
        sch = sql_identifier(schema)
        tbl = sql_identifier(table)
        idx = sql_identifier(idx_name)
        op.execute(
            sa.text('CREATE INDEX IF NOT EXISTS :idx ON :sch.:tbl (:cols) WHERE :where'),
            {"idx": idx, "sch": sch, "tbl": tbl, "cols": col_list, "where": where_clause},
        )


def downgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        return

    # Drop partial indexes (in reverse)
    for schema, table, idx_name, _columns, _where in reversed(PARTIAL_INDEXES):
        sch = sql_identifier(schema)
        idx = sql_identifier(idx_name)
        op.execute(
            sa.text('DROP INDEX IF EXISTS :sch.:idx'),
            {"sch": sch, "idx": idx},
        )

    # Drop composite indexes (in reverse)
    for schema, table, idx_name, _columns in reversed(COMPOSITE_INDEXES):
        sch = sql_identifier(schema)
        idx = sql_identifier(idx_name)
        op.execute(
            sa.text('DROP INDEX IF EXISTS :sch.:idx'),
            {"sch": sch, "idx": idx},
        )
