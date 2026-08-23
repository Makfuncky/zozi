"""rename supplier tables to plural names (Law 6)

Law 6 (ARCHITECTURE_DIAGRAM.md 8): naming lint requires plural table names.
Three supplier-domain tables were created with singular names; this migration
renames them to their canonical plural forms.

Affected tables (all in schema='suppliers'):
- supplier_badge_catalog -> supplier_badge_catalogs
- supplier_badge_billing_history -> supplier_badge_billing_histories
- supplier_onboarding_sync -> supplier_onboarding_syncs

Revision ID: 20260822_pluralize_supplier_table_names
Revises: 20260822_supplier_to_suppliers_schema
Create Date: 2026-08-22
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260822_pluralize_supplier_table_names"
down_revision: Union[str, None] = "20260822_supplier_to_suppliers_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        return

    # Rename tables to plural forms (Law 6)
    op.rename_table("supplier_badge_catalog", "supplier_badge_catalogs", schema="suppliers")
    op.rename_table("supplier_badge_billing_history", "supplier_badge_billing_histories", schema="suppliers")
    op.rename_table("supplier_onboarding_sync", "supplier_onboarding_syncs", schema="suppliers")


def downgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        return

    op.rename_table("supplier_badge_catalogs", "supplier_badge_catalog", schema="suppliers")
    op.rename_table("supplier_badge_billing_histories", "supplier_badge_billing_history", schema="suppliers")
    op.rename_table("supplier_onboarding_syncs", "supplier_onboarding_sync", schema="suppliers")
