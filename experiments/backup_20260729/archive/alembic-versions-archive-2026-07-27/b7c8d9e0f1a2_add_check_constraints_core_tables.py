"""add_check_constraints_core_tables

Revision ID: b7c8d9e0f1a2
Revises: 78b323427448
Create Date: 2026-03-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'b7c8d9e0f1a2'
down_revision: Union[str, Sequence[str], None] = '78b323427448'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _get_check_names(inspector, table_name: str) -> set[str]:
    if not _table_exists(inspector, table_name):
        return set()
    return {constraint.get('name') for constraint in inspector.get_check_constraints(table_name)}


def _add_checks(table_name: str, checks: list[tuple[str, str]], inspector) -> None:
    if not _table_exists(inspector, table_name):
        return
    existing = _get_check_names(inspector, table_name)
    with op.batch_alter_table(table_name, schema=None) as batch_op:
        for name, condition in checks:
            if name not in existing:
                batch_op.create_check_constraint(name, condition)


def _drop_checks(table_name: str, checks: list[tuple[str, str]], inspector) -> None:
    if not _table_exists(inspector, table_name):
        return
    existing = _get_check_names(inspector, table_name)
    with op.batch_alter_table(table_name, schema=None) as batch_op:
        for name, _condition in checks:
            if name in existing:
                batch_op.drop_constraint(name, type_='check')


def upgrade() -> None:
    bind = op.get_bind()
    # SQLite does not enforce CHECK constraints by default and batch_alter_table
    # can't drop FK-referenced tables. Skip on SQLite; constraints enforced on PostgreSQL.
    if bind.dialect.name == "sqlite":
        return
    inspector = inspect(bind)

    checks_by_table: dict[str, list[tuple[str, str]]] = {
        'products': [
            ('ck_products_price_nonnegative', 'price >= 0'),
            ('ck_products_stock_nonnegative', 'stock >= 0'),
            ('ck_products_compare_price_nonnegative', 'compare_price IS NULL OR compare_price >= 0'),
            ('ck_products_rating_range', 'rating >= 0 AND rating <= 5'),
            ('ck_products_sales_count_nonnegative', 'sales_count >= 0'),
        ],
        'orders': [
            ('ck_orders_subtotal_nonnegative', 'subtotal_amount IS NULL OR subtotal_amount >= 0'),
            ('ck_orders_discount_nonnegative', 'discount_amount >= 0'),
            ('ck_orders_vat_nonnegative', 'vat_amount >= 0'),
            ('ck_orders_shipping_nonnegative', 'shipping_amount >= 0'),
            ('ck_orders_total_nonnegative', 'total_amount >= 0'),
        ],
        'order_items': [
            ('ck_order_items_quantity_positive', 'quantity > 0'),
            ('ck_order_items_price_nonnegative', 'price >= 0'),
        ],
        'reviews': [
            ('ck_reviews_rating_range', 'rating >= 1 AND rating <= 5'),
        ],
        'coupons': [
            ('ck_coupons_value_nonnegative', 'value >= 0'),
            ('ck_coupons_min_order_nonnegative', 'min_order >= 0'),
            ('ck_coupons_uses_count_nonnegative', 'uses_count >= 0'),
            ('ck_coupons_max_uses_nonnegative', 'max_uses IS NULL OR max_uses >= 0'),
            ("ck_coupons_discount_type_valid", "discount_type IN ('percent','fixed')"),
        ],
        'cart_items': [
            ('ck_cart_items_quantity_positive', 'quantity > 0'),
        ],
        'payouts': [
            ('ck_payouts_amount_nonnegative', 'amount >= 0'),
        ],
        'shipping_zones': [
            ('ck_shipping_zones_base_price_nonnegative', 'base_price >= 0'),
            ('ck_shipping_zones_price_per_kg_nonnegative', 'price_per_kg >= 0'),
            ('ck_shipping_zones_free_shipping_above_nonnegative', 'free_shipping_above IS NULL OR free_shipping_above >= 0'),
            ('ck_shipping_zones_estimated_days_min_nonnegative', 'estimated_days_min IS NULL OR estimated_days_min >= 0'),
            ('ck_shipping_zones_estimated_days_max_nonnegative', 'estimated_days_max IS NULL OR estimated_days_max >= 0'),
            ('ck_shipping_zones_estimated_days_min_le_max', 'estimated_days_min IS NULL OR estimated_days_max IS NULL OR estimated_days_min <= estimated_days_max'),
        ],
        'flash_sales': [
            ('ck_flash_sales_discount_pct_range', 'discount_pct >= 0 AND discount_pct <= 100'),
        ],
    }

    for table_name, checks in checks_by_table.items():
        _add_checks(table_name, checks, inspector)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    checks_by_table: dict[str, list[tuple[str, str]]] = {
        'flash_sales': [
            ('ck_flash_sales_discount_pct_range', 'discount_pct >= 0 AND discount_pct <= 100'),
        ],
        'shipping_zones': [
            ('ck_shipping_zones_estimated_days_min_le_max', 'estimated_days_min IS NULL OR estimated_days_max IS NULL OR estimated_days_min <= estimated_days_max'),
            ('ck_shipping_zones_estimated_days_max_nonnegative', 'estimated_days_max IS NULL OR estimated_days_max >= 0'),
            ('ck_shipping_zones_estimated_days_min_nonnegative', 'estimated_days_min IS NULL OR estimated_days_min >= 0'),
            ('ck_shipping_zones_free_shipping_above_nonnegative', 'free_shipping_above IS NULL OR free_shipping_above >= 0'),
            ('ck_shipping_zones_price_per_kg_nonnegative', 'price_per_kg >= 0'),
            ('ck_shipping_zones_base_price_nonnegative', 'base_price >= 0'),
        ],
        'payouts': [
            ('ck_payouts_amount_nonnegative', 'amount >= 0'),
        ],
        'cart_items': [
            ('ck_cart_items_quantity_positive', 'quantity > 0'),
        ],
        'coupons': [
            ("ck_coupons_discount_type_valid", "discount_type IN ('percent','fixed')"),
            ('ck_coupons_max_uses_nonnegative', 'max_uses IS NULL OR max_uses >= 0'),
            ('ck_coupons_uses_count_nonnegative', 'uses_count >= 0'),
            ('ck_coupons_min_order_nonnegative', 'min_order >= 0'),
            ('ck_coupons_value_nonnegative', 'value >= 0'),
        ],
        'reviews': [
            ('ck_reviews_rating_range', 'rating >= 1 AND rating <= 5'),
        ],
        'order_items': [
            ('ck_order_items_price_nonnegative', 'price >= 0'),
            ('ck_order_items_quantity_positive', 'quantity > 0'),
        ],
        'orders': [
            ('ck_orders_total_nonnegative', 'total_amount >= 0'),
            ('ck_orders_shipping_nonnegative', 'shipping_amount >= 0'),
            ('ck_orders_vat_nonnegative', 'vat_amount >= 0'),
            ('ck_orders_discount_nonnegative', 'discount_amount >= 0'),
            ('ck_orders_subtotal_nonnegative', 'subtotal_amount IS NULL OR subtotal_amount >= 0'),
        ],
        'products': [
            ('ck_products_sales_count_nonnegative', 'sales_count >= 0'),
            ('ck_products_rating_range', 'rating >= 0 AND rating <= 5'),
            ('ck_products_compare_price_nonnegative', 'compare_price IS NULL OR compare_price >= 0'),
            ('ck_products_stock_nonnegative', 'stock >= 0'),
            ('ck_products_price_nonnegative', 'price >= 0'),
        ],
    }

    for table_name, checks in checks_by_table.items():
        _drop_checks(table_name, checks, inspector)

