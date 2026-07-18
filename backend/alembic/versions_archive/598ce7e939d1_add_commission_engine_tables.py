"""add_commission_engine_tables

Revision ID: 598ce7e939d1
Revises: c1d2e3f4a5b6
Create Date: 2026-04-06 19:01:54.222319
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = "598ce7e939d1"
down_revision: Union[str, Sequence[str], None] = "c1d2e3f4a5b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(table_name: str) -> bool:
    return table_name in set(inspect(op.get_bind()).get_table_names())


def _index_names(table_name: str) -> set[str]:
    if not _table_exists(table_name):
        return set()
    return {
        str(index["name"])
        for index in inspect(op.get_bind()).get_indexes(table_name)
        if index.get("name")
    }


def upgrade() -> None:
    if not _table_exists("commission_global_config"):
        op.create_table(
            "commission_global_config",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("default_rate", sa.Numeric(precision=5, scale=4), nullable=False),
            sa.Column("low_value_threshold", sa.Numeric(precision=12, scale=2), nullable=False),
            sa.Column("fixed_cap_amount", sa.Numeric(precision=12, scale=2), nullable=False),
            sa.Column("fixed_cap_enabled", sa.Boolean(), nullable=False),
            sa.Column("margin_protection_enabled", sa.Boolean(), nullable=False),
            sa.Column("margin_threshold", sa.Numeric(precision=5, scale=4), nullable=True),
            sa.Column("updated_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.CheckConstraint("default_rate >= 0 AND default_rate <= 1", name="ck_cgc_default_rate_valid"),
            sa.CheckConstraint("fixed_cap_amount >= 0", name="ck_cgc_fixed_cap_amount_nonneg"),
            sa.CheckConstraint("low_value_threshold >= 0", name="ck_cgc_low_value_threshold_nonneg"),
            sa.PrimaryKeyConstraint("id"),
        )
    if "ix_commission_global_config_id" not in _index_names("commission_global_config"):
        op.create_index("ix_commission_global_config_id", "commission_global_config", ["id"], unique=False)

    if not _table_exists("commission_category_rates"):
        op.create_table(
            "commission_category_rates",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("category_slug", sa.String(length=100), nullable=False),
            sa.Column("category_display_name", sa.String(length=150), nullable=False),
            sa.Column("rate", sa.Numeric(precision=5, scale=4), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("updated_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.CheckConstraint("rate >= 0 AND rate <= 1", name="ck_ccr_rate_valid"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("category_slug", name="uq_commission_category_rates_slug"),
        )
    existing_category_indexes = _index_names("commission_category_rates")
    if "ix_commission_category_rates_active" not in existing_category_indexes:
        op.create_index(
            "ix_commission_category_rates_active",
            "commission_category_rates",
            ["is_active", "category_slug"],
            unique=False,
        )
    if "ix_commission_category_rates_category_slug" not in existing_category_indexes:
        op.create_index(
            "ix_commission_category_rates_category_slug",
            "commission_category_rates",
            ["category_slug"],
            unique=True,
        )
    if "ix_commission_category_rates_id" not in existing_category_indexes:
        op.create_index("ix_commission_category_rates_id", "commission_category_rates", ["id"], unique=False)

    if not _table_exists("commission_badge_tiers"):
        op.create_table(
            "commission_badge_tiers",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("badge_level", sa.String(length=30), nullable=False),
            sa.Column("commission_rate", sa.Numeric(precision=5, scale=4), nullable=False),
            sa.Column("setup_fee", sa.Numeric(precision=12, scale=3), nullable=False),
            sa.Column("recurring_fee", sa.Numeric(precision=12, scale=3), nullable=False),
            sa.Column("recurring_interval", sa.String(length=20), nullable=True),
            sa.Column("benefits_json", sa.Text(), nullable=True),
            sa.Column("min_fulfilled_orders", sa.Integer(), nullable=True),
            sa.Column("min_monthly_revenue", sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column("sort_order", sa.Integer(), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("updated_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.CheckConstraint("commission_rate >= 0 AND commission_rate <= 1", name="ck_cbt_rate_valid"),
            sa.CheckConstraint("recurring_fee >= 0", name="ck_cbt_recurring_fee_nonneg"),
            sa.CheckConstraint("setup_fee >= 0", name="ck_cbt_setup_fee_nonneg"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("badge_level", name="uq_commission_badge_tiers_level"),
        )
    existing_badge_indexes = _index_names("commission_badge_tiers")
    if "ix_commission_badge_tiers_badge_level" not in existing_badge_indexes:
        op.create_index("ix_commission_badge_tiers_badge_level", "commission_badge_tiers", ["badge_level"], unique=True)
    if "ix_commission_badge_tiers_id" not in existing_badge_indexes:
        op.create_index("ix_commission_badge_tiers_id", "commission_badge_tiers", ["id"], unique=False)

    if not _table_exists("commission_ledger_entries"):
        op.create_table(
            "commission_ledger_entries",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id"), nullable=False),
            sa.Column("order_item_id", sa.Integer(), sa.ForeignKey("order_items.id"), nullable=True),
            sa.Column("supplier_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id"), nullable=True),
            sa.Column("category_slug", sa.String(length=100), nullable=True),
            sa.Column("badge_level", sa.String(length=30), nullable=True),
            sa.Column("global_default_rate", sa.Numeric(precision=5, scale=4), nullable=True),
            sa.Column("category_rate", sa.Numeric(precision=5, scale=4), nullable=True),
            sa.Column("badge_rate", sa.Numeric(precision=5, scale=4), nullable=True),
            sa.Column("override_rate", sa.Numeric(precision=5, scale=4), nullable=True),
            sa.Column("applied_rate", sa.Numeric(precision=5, scale=4), nullable=False),
            sa.Column("calculation_method", sa.String(length=30), nullable=False),
            sa.Column("order_value", sa.Numeric(precision=12, scale=2), nullable=False),
            sa.Column("commission_pct", sa.Numeric(precision=12, scale=3), nullable=False),
            sa.Column("cap_applied", sa.Boolean(), nullable=False),
            sa.Column("commission_amount", sa.Numeric(precision=12, scale=3), nullable=False),
            sa.Column("low_value_threshold_used", sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column("fixed_cap_used", sa.Numeric(precision=12, scale=3), nullable=True),
            sa.Column("override_flag", sa.Boolean(), nullable=False),
            sa.Column("is_adjusted", sa.Boolean(), nullable=False),
            sa.Column("adjusted_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("adjusted_at", sa.DateTime(), nullable=True),
            sa.Column("adjustment_reason", sa.Text(), nullable=True),
            sa.Column("original_commission_amount", sa.Numeric(precision=12, scale=3), nullable=True),
            sa.Column("currency", sa.String(length=10), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.CheckConstraint(
                "calculation_method IN ('override','category','badge','global_default')",
                name="ck_cle_calc_method_valid",
            ),
            sa.CheckConstraint("applied_rate >= 0 AND applied_rate <= 1", name="ck_cle_applied_rate_valid"),
            sa.CheckConstraint("commission_amount >= 0", name="ck_cle_commission_amount_nonneg"),
            sa.CheckConstraint("order_value >= 0", name="ck_cle_order_value_nonneg"),
            sa.PrimaryKeyConstraint("id"),
        )
    existing_ledger_indexes = _index_names("commission_ledger_entries")
    ledger_indexes = {
        "ix_cle_order_item": ["order_item_id"],
        "ix_cle_order_supplier": ["order_id", "supplier_id"],
        "ix_cle_supplier_created": ["supplier_id", "created_at"],
        "ix_commission_ledger_entries_id": ["id"],
        "ix_commission_ledger_entries_order_id": ["order_id"],
        "ix_commission_ledger_entries_supplier_id": ["supplier_id"],
        "ix_commission_ledger_entries_created_at": ["created_at"],
    }
    for index_name, columns in ledger_indexes.items():
        if index_name not in existing_ledger_indexes:
            op.create_index(index_name, "commission_ledger_entries", columns, unique=False)


def downgrade() -> None:
    if _table_exists("commission_ledger_entries"):
        existing_ledger_indexes = _index_names("commission_ledger_entries")
        for index_name in [
            "ix_cle_order_item",
            "ix_cle_order_supplier",
            "ix_cle_supplier_created",
            "ix_commission_ledger_entries_id",
            "ix_commission_ledger_entries_order_id",
            "ix_commission_ledger_entries_supplier_id",
            "ix_commission_ledger_entries_created_at",
        ]:
            if index_name in existing_ledger_indexes:
                op.drop_index(index_name, table_name="commission_ledger_entries")
        op.drop_table("commission_ledger_entries")

    if _table_exists("commission_badge_tiers"):
        existing_badge_indexes = _index_names("commission_badge_tiers")
        for index_name in ["ix_commission_badge_tiers_badge_level", "ix_commission_badge_tiers_id"]:
            if index_name in existing_badge_indexes:
                op.drop_index(index_name, table_name="commission_badge_tiers")
        op.drop_table("commission_badge_tiers")

    if _table_exists("commission_category_rates"):
        existing_category_indexes = _index_names("commission_category_rates")
        for index_name in [
            "ix_commission_category_rates_active",
            "ix_commission_category_rates_category_slug",
            "ix_commission_category_rates_id",
        ]:
            if index_name in existing_category_indexes:
                op.drop_index(index_name, table_name="commission_category_rates")
        op.drop_table("commission_category_rates")

    if _table_exists("commission_global_config"):
        existing_global_indexes = _index_names("commission_global_config")
        if "ix_commission_global_config_id" in existing_global_indexes:
            op.drop_index("ix_commission_global_config_id", table_name="commission_global_config")
        op.drop_table("commission_global_config")

