"""rename supplier schema to suppliers (plural) (S5 + SUPPLIERS-SCHEMA-NAME)

Law 6 (ARCHITECTURE_DIAGRAM.md 9): every domain maps to one Postgres schema.
The supplier domain tables were declared under the singular schema='supplier';
the canonical name is 'suppliers' (plural, matching the domain name).

This migration is PostgreSQL-only (ALTER SCHEMA ... RENAME TO). On SQLite (dev)
the ORM + create_all already produce the correctly-named tables under the
declared schema, so this migration is a no-op there.

Affected tables (all currently in schema='supplier', moving to schema='suppliers'):
- supplier_profiles, supplier_documents, supplier_notification_preferences,
  supplier_badge_catalog, supplier_badges, supplier_badge_billing_history,
  supplier_onboarding_sync (from suppliers/models/suppliers.py)
- supplier_bank_accounts, supplier_disputes, supplier_country_commissions
  (from governance/models/admin.py)
- supplier_fraud_indicators (from governance/models/fraud.py)

Revision ID: 20260822_supplier_to_suppliers_schema
Revises: 20260822_governance_schema_consolidation
Create Date: 2026-08-22
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260822_supplier_to_suppliers_schema"
down_revision: Union[str, None] = "20260822_governance_schema_consolidation"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Tables currently in schema='supplier' that move to schema='suppliers'
_MOVES = [
    # suppliers/models/suppliers.py
    ("supplier_profiles", "supplier"),
    ("supplier_documents", "supplier"),
    ("supplier_notification_preferences", "supplier"),
    ("supplier_badge_catalog", "supplier"),
    ("supplier_badges", "supplier"),
    ("supplier_badge_billing_history", "supplier"),
    ("supplier_onboarding_sync", "supplier"),
    # governance/models/admin.py
    ("supplier_bank_accounts", "supplier"),
    ("supplier_disputes", "supplier"),
    ("supplier_country_commissions", "supplier"),
    # governance/models/fraud.py
    ("supplier_fraud_indicators", "supplier"),
]


def _exec(sql: str) -> None:
    op.execute(sa.text(sql))


def upgrade() -> None:
    if op.get_context().dialect.name != "postgresql":
        return
    # Rename the entire schema (atomic, moves all objects at once)
    _exec("ALTER SCHEMA IF EXISTS supplier RENAME TO suppliers")


def downgrade() -> None:
    if op.get_context().dialect.name != "postgresql":
        return
    _exec("ALTER SCHEMA IF EXISTS suppliers RENAME TO supplier")
