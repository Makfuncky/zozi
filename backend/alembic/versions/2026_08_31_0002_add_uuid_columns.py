"""Add UUID columns to core tables

Revision ID: 20260831_0002
Revises: 20260831_0001
Create Date: 2026-08-31
"""
import sqlalchemy as sa
from typing import Sequence, Union

from alembic import op
from sqlalchemy.sql import quoted_name as sql_identifier

revision: str = "20260831_0002"
down_revision: Union[str, None] = "20260831_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Core tables that need UUID columns (ordered by priority)
CORE_TABLES = [
    # Core identity
    ("core", "users"),
    ("core", "user_sessions"),
    ("core", "user_devices"),
    ("core", "user_login_history"),
    # Commerce
    ("commerce", "products"),
    ("commerce", "product_variants"),
    ("commerce", "categories"),
    ("commerce", "carts"),
    ("commerce", "cart_items"),
    ("commerce", "orders"),
    ("commerce", "order_items"),
    ("commerce", "banners"),
    ("commerce", "coupons"),
    ("commerce", "flash_sales"),
    ("commerce", "flash_sale_items"),
    ("commerce", "reviews"),
    # Customer
    ("customer", "customers"),
    ("customer", "addresses"),
    ("customer", "wishlists"),
    ("customer", "wishlist_items"),
    # Supplier
    ("supplier", "supplier_profiles"),
    ("supplier", "supplier_documents"),
    # Logistics
    ("logistics", "logistics_partners"),
    ("logistics", "logistics_partner_documents"),
    ("logistics", "logistics_partner_service_areas"),
    ("logistics", "logistics_pricing_profiles"),
    ("logistics", "logistics_vehicle_rules"),
    ("logistics", "shipments"),
    ("logistics", "shipment_events"),
    # Finance
    ("finance", "accounts"),
    ("finance", "account_groups"),
    ("finance", "journal_entries"),
    ("finance", "journal_entry_lines"),
    ("finance", "ap_ledger_entries"),
    ("finance", "ar_ledger_entries"),
    ("finance", "invoices"),
    ("finance", "invoice_items"),
    ("finance", "payments"),
    # Treasury
    ("treasury", "treasury_accounts"),
    ("treasury", "treasury_transactions"),
    ("treasury", "cash_accounts"),
    ("treasury", "bank_accounts"),
    ("treasury", "payout_batches"),
    ("treasury", "payouts"),
    # HR
    ("hr", "employees"),
    ("hr", "employee_addresses"),
    ("hr", "employee_attendance"),
    ("hr", "employee_leave_requests"),
    ("hr", "employee_shift_rosters"),
    ("hr", "offices"),
    # Country
    ("country", "country_configs"),
    ("country", "country_cities"),
    ("country", "country_commission_rates"),
    ("country", "country_staff_assignments"),
    # Communication
    ("comms", "notifications"),
    ("comms", "messages"),
    ("comms", "email_campaigns"),
    ("comms", "email_templates"),
    ("comms", "chat_threads"),
    ("comms", "chat_messages"),
    ("comms", "chat_attachments"),
    ("comms", "support_tickets"),
    # Security
    ("security", "api_keys"),
    ("security", "fraud_alerts"),
    ("security", "fraud_cases"),
    ("security", "fraud_rules"),
    ("security", "fraud_blacklist"),
    ("security", "ip_reputations"),
    ("security", "device_fingerprints"),
    # Audit
    ("audit", "audit_logs"),
    # AI
    ("ai", "ai_staging_products"),
    ("ai", "ai_upload_jobs"),
    # Media
    ("media", "media_assets"),
    # Configuration
    ("configuration", "system_settings"),
    ("configuration", "country_feature_flags"),
]


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        # SQLite: add columns without schema prefix
        for _schema, table in CORE_TABLES:
            tbl = sql_identifier(table)
            try:
                op.execute(
                    sa.text('ALTER TABLE :tbl ADD COLUMN uuid CHAR(36)'),
                    {"tbl": tbl},
                )
                op.execute(
                    sa.text('UPDATE :tbl SET uuid = lower(hex(randomblob(16))) WHERE uuid IS NULL'),
                    {"tbl": tbl},
                )
            except Exception:
                pass  # Column may already exist
        return

    # NEON: add columns with schema prefix
    for schema, table in CORE_TABLES:
        sch = sql_identifier(schema)
        tbl = sql_identifier(table)
        try:
            op.execute(
                sa.text('ALTER TABLE :sch.:tbl ADD COLUMN IF NOT EXISTS uuid UUID'),
                {"sch": sch, "tbl": tbl},
            )
            op.execute(
                sa.text('UPDATE :sch.:tbl SET uuid = gen_random_uuid() WHERE uuid IS NULL'),
                {"sch": sch, "tbl": tbl},
            )
            op.execute(
                sa.text('ALTER TABLE :sch.:tbl ALTER COLUMN uuid SET NOT NULL'),
                {"sch": sch, "tbl": tbl},
            )
            idx = sql_identifier(f"ix_{table}_uuid")
            op.execute(
                sa.text('CREATE UNIQUE INDEX IF NOT EXISTS :idx ON :sch.:tbl (uuid)'),
                {"idx": idx, "sch": sch, "tbl": tbl},
            )
        except Exception:
            pass  # Column may already exist


def downgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        return  # SQLite doesn't support DROP COLUMN easily

    for schema, table in reversed(CORE_TABLES):
        sch = sql_identifier(schema)
        tbl = sql_identifier(table)
        try:
            op.execute(
                sa.text('ALTER TABLE :sch.:tbl DROP COLUMN IF EXISTS uuid'),
                {"sch": sch, "tbl": tbl},
            )
        except Exception:
            pass
