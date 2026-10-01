"""split the oversized ``commerce`` schema into per-domain schemas

Data-preserving migration. The 29 tables that accumulated in the catch-all
``commerce`` schema are moved into their correct bounded-context schemas:

- catalog:        categories, products, reviews, product_variants,
                  product_filter_metadata, product_filter_options,
                  product_verifications
- promotion:      flash_sales, flash_sale_items, coupons, banners, coupon_usage,
                  promotion_engine_configs, promotion_ledger_entries,
                  promotion_order_tiers
- loyalty:        points_transactions, user_points, badge_billing_records,
                  badge_transactions, badge_tiers, commission_badge_tiers,
                  commission_global_configs
- finance:        commission_agreements, product_commission_overrides,
                  commission_ledger_entries, commission_category_rates
- customer:       carts, cart_items
- security:       return_abuse_patterns

PostgreSQL moves each table (with its indexes, constraints, owned sequences
and cross-references) atomically via ``ALTER TABLE ... SET SCHEMA`` -- no data
is rewritten. The statements are guarded with ``IF EXISTS`` so the migration is
idempotent and safe to re-run on a DB that was already upgraded (or built from
scratch, since the earlier migrations still create these tables under
``commerce`` first).

On SQLite (dev) the ORM + ``create_all`` already produce the correctly-named
tables, so this migration is a no-op there.

Revision ID: 20260821_split_commerce
Revises: 20260811_otp_codes
Create Date: 2026-08-21
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260821_split_commerce"
down_revision: Union[str, None] = "20260811_otp_codes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (table, target_schema) -- 29 tables currently living in ``commerce``
_MOVES = [
    ("categories", "catalog"),
    ("products", "catalog"),
    ("reviews", "catalog"),
    ("product_variants", "catalog"),
    ("product_filter_metadata", "catalog"),
    ("product_filter_options", "catalog"),
    ("product_verifications", "catalog"),
    ("flash_sales", "promotion"),
    ("flash_sale_items", "promotion"),
    ("coupons", "promotion"),
    ("banners", "promotion"),
    ("coupon_usage", "promotion"),
    ("promotion_engine_configs", "promotion"),
    ("promotion_ledger_entries", "promotion"),
    ("promotion_order_tiers", "promotion"),
    ("points_transactions", "loyalty"),
    ("user_points", "loyalty"),
    ("badge_billing_records", "loyalty"),
    ("badge_transactions", "loyalty"),
    ("badge_tiers", "loyalty"),
    ("commission_badge_tiers", "loyalty"),
    ("commission_global_configs", "loyalty"),
    ("commission_agreements", "finance"),
    ("product_commission_overrides", "finance"),
    ("commission_ledger_entries", "finance"),
    ("commission_category_rates", "finance"),
    ("carts", "customer"),
    ("cart_items", "customer"),
    ("return_abuse_patterns", "security"),
]

_TARGET_SCHEMAS = sorted({schema for _, schema in _MOVES})


def _exec(sql: str) -> None:
    op.execute(sa.text(sql))


def upgrade() -> None:
    if op.get_context().dialect.name != "postgresql":
        return

    for schema in _TARGET_SCHEMAS:
        _exec(f"CREATE SCHEMA IF NOT EXISTS {schema}")

    for table, schema in _MOVES:
        # Idempotent: a fresh DB (or an already-upgraded one) may not have the
        # table under ``commerce`` anymore, in which case this is a no-op.
        _exec(
            "ALTER TABLE IF EXISTS commerce.{t} SET SCHEMA {s}".format(t=table, s=schema)
        )


def downgrade() -> None:
    if op.get_context().dialect.name != "postgresql":
        return

    _exec("CREATE SCHEMA IF NOT EXISTS commerce")
    for table, schema in _MOVES:
        _exec(
            "ALTER TABLE IF EXISTS {s}.{t} SET SCHEMA commerce".format(s=schema, t=table)
        )
