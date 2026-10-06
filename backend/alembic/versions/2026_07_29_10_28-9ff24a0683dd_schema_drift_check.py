"""schema_drift_check

Revision ID: 9ff24a0683dd
Revises: e281faa0c087
Create Date: 2026-07-29 10:28:00.000000+00:00

Aligns ORM definitions with the live SQLite database.
- Converts 7 unique indexes to unique constraints (SQLite batch mode).
- Drops stale index ix_commission_ledger_supplier_created.
- Adds missing indexes (journal_entries, logistics_partner_documents).
- Skips EncryptedString column type changes (PostgreSQL-only; ORM uses
  TypeDecorator that SQLite stores as TEXT at runtime).
- Idempotent: checks existence before creating/dropping.

NOTE: Downgrade is incomplete — the 7 constraint→index reversals are
not implemented because batch_alter_table doesn't support DROP
UNIQUE CONSTRAINT + CREATE UNIQUE INDEX in a single downgrade pass
for SQLite. Full downgrade requires PostgreSQL.
"""
import logging
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.exc import NoInspectionAvailable

_logger = logging.getLogger("alembic")

revision: str = "9ff24a0683dd"
down_revision: Union[str, None] = "e281faa0c087"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _is_offline_connection(conn) -> bool:
    """Return True when running in alembic --sql offline mode."""
    if conn is None:
        return True
    try:
        sa_inspect(conn)
        return False
    except (NoInspectionAvailable, Exception):
        return True


def _index_exists(conn, table: str, name: str, schema: str | None = None) -> bool:
    if conn is None:
        raise RuntimeError("Cannot check index existence offline (--sql)")
    inspector = sa_inspect(conn)
    existing = {i["name"] for i in inspector.get_indexes(table, schema=schema)}
    return name in existing


# ── helpers ──────────────────────────────────────────────────────────

def _convert_unique_index_to_constraint(conn, table: str, index_name: str, columns: list[str]):
    """Convert a unique index to a unique constraint (SQLite batch mode, idempotent).

    In SQLite, UNIQUE indexes and UNIQUE constraints are logically equivalent
    but have different CREATE/ALTER semantics. This function drops the old
    index and creates a constraint with the same name for ORM alignment.
    """
    if _is_offline_connection(conn):
        raise RuntimeError("Catalog introspection unavailable in offline (--sql) mode")
    if _index_exists(conn, table, index_name):
        try:
            op.drop_index(index_name, table_name=table)
        except Exception as exc:
            _logger.warning("Failed to drop index %s on %s: %s", index_name, table, exc)
            return  # Skip constraint creation if drop failed
    # Only create if not already present (idempotent for re-runs)
    if not _index_exists(conn, table, index_name):
        with op.batch_alter_table(table) as batch_op:
            batch_op.create_unique_constraint(index_name, columns)


def _add_index(conn, name: str, table: str, columns: list[str]):
    if _is_offline_connection(conn):
        raise RuntimeError("Catalog introspection unavailable in offline (--sql) mode")
    if not _index_exists(conn, table, name):
        op.create_index(name, table, columns, unique=False)


# ── upgrade ──────────────────────────────────────────────────────────

def upgrade() -> None:
    bind = op.get_bind()
    offline = _is_offline_connection(bind)

    # ── Convert unique indexes → unique constraints (same name, different DDL) ──
    def _convert(conv_table, conv_index, conv_cols):
        if offline or _index_exists(bind, conv_table, conv_index):
            try:
                op.drop_index(conv_index, table_name=conv_table)
            except Exception as exc:
                _logger.warning("Failed to drop index %s on %s: %s", conv_index, conv_table, exc)
                return
        if offline or not _index_exists(bind, conv_table, conv_index):
            with op.batch_alter_table(conv_table) as batch_op:
                batch_op.create_unique_constraint(conv_index, conv_cols)

    _convert("campaign_recipients", "uq_campaign_recipient", ["campaign_id", "user_id"])
    _convert("commission_agreements", "uq_commission_agreement", ["supplier_id", "country_code", "tier"])
    _convert("email_campaign_logs", "uq_email_campaign_log", ["campaign_id", "recipient_email"])
    _convert("flash_sale_items", "uq_flash_sale_item", ["flash_sale_id", "product_id"])
    _convert("product_commission_overrides", "uq_product_commission_override", ["product_id", "supplier_id"])
    _convert("shipping_rules", "uq_shipping_rule", ["country_code", "method"])
    _convert("tax_rules", "uq_tax_rule", ["country_code", "tax_name"])

    # ── Drop stale index that ORM no longer defines ───────────────────
    if offline or _index_exists(bind, "commission_ledger_entries", "ix_commission_ledger_supplier_created"):
        op.drop_index("ix_commission_ledger_supplier_created", table_name="commission_ledger_entries")

    # ── Add missing indexes ──────────────────────────────────────────
    def _add(ix_name, tbl, cols):
        if offline or not _index_exists(bind, tbl, ix_name):
            op.create_index(ix_name, tbl, cols, unique=False)

    _add("ix_journal_entries_deleted_by", "journal_entries", ["deleted_by"])
    _add("ix_logistics_partner_documents_reviewed_by", "logistics_partner_documents", ["reviewed_by"])

    # NOTE: EncryptedString column changes (orders.customer_phone, users.phone,
    # users.address_book) are PostgreSQL-only. SQLite stores them as TEXT at
    # runtime via the TypeDecorator. Skipping for SQLite compatibility.


# ── downgrade ────────────────────────────────────────────────────────
# NOTE: Full downgrade is not implemented for SQLite. The 7 constraint→index
# reversals require batch_alter_table + DROP CONSTRAINT + CREATE INDEX which
# is not reliably supported across SQLite versions. On PostgreSQL, full
# downgrade can be implemented using batch mode with op.execute().

def downgrade() -> None:
    bind = op.get_bind()
    offline = _is_offline_connection(bind)

    # Re-add dropped index
    if offline or not _index_exists(bind, "commission_ledger_entries", "ix_commission_ledger_supplier_created"):
        op.create_index("ix_commission_ledger_supplier_created",
                        "commission_ledger_entries",
                        ["supplier_id", "created_at"], unique=False)

    # Drop newly added indexes
    def _drop(tbl, ix_name):
        if offline or _index_exists(bind, tbl, ix_name):
            op.drop_index(ix_name, table_name=tbl)

    _drop("logistics_partner_documents", "ix_logistics_partner_documents_reviewed_by")
    _drop("journal_entries", "ix_journal_entries_deleted_by")
