"""Add version columns to core tables for optimistic locking

Revision ID: 20260831_0003
Revises: 20260831_0002
Create Date: 2026-08-31
"""
from typing import Sequence, Union

from alembic import op

revision: str = "20260831_0003"
down_revision: Union[str, None] = "20260831_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Tables that need version columns (high-contention tables)
VERSION_TABLES = [
    # Core identity
    ("core", "users"),
    # Commerce (high contention)
    ("commerce", "products"),
    ("commerce", "product_variants"),
    ("commerce", "carts"),
    ("commerce", "cart_items"),
    ("commerce", "orders"),
    ("commerce", "order_items"),
    ("commerce", "coupons"),
    ("commerce", "flash_sales"),
    ("commerce", "flash_sale_items"),
    # Customer
    ("customer", "customers"),
    ("customer", "wishlists"),
    ("customer", "wishlist_items"),
    # Supplier
    ("supplier", "supplier_profiles"),
    # Logistics
    ("logistics", "logistics_partners"),
    ("logistics", "shipments"),
    # Finance (high contention)
    ("finance", "accounts"),
    ("finance", "journal_entries"),
    ("finance", "ap_ledger_entries"),
    ("finance", "ar_ledger_entries"),
    # Treasury
    ("treasury", "treasury_accounts"),
    ("treasury", "payout_batches"),
    # HR
    ("hr", "employees"),
    ("hr", "employee_attendance"),
    ("hr", "employee_leave_requests"),
    # Country
    ("country", "country_configs"),
    # Security
    ("security", "fraud_alerts"),
    ("security", "fraud_cases"),
]


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        # SQLite: add columns without schema prefix
        for _schema, table in VERSION_TABLES:
            try:
                op.execute(
                    f'ALTER TABLE "{table}" ADD COLUMN version INTEGER NOT NULL DEFAULT 1'
                )
            except Exception:
                pass  # Column may already exist
        return

    # NEON: add columns with schema prefix
    for schema, table in VERSION_TABLES:
        try:
            op.execute(
                f'ALTER TABLE "{schema}"."{table}" ADD COLUMN IF NOT EXISTS version '
                f'INTEGER NOT NULL DEFAULT 1'
            )
        except Exception:
            pass  # Column may already exist


def downgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        return  # SQLite doesn't support DROP COLUMN easily

    for schema, table in reversed(VERSION_TABLES):
        try:
            op.execute(
                f'ALTER TABLE "{schema}"."{table}" DROP COLUMN IF EXISTS version'
            )
        except Exception:
            pass
