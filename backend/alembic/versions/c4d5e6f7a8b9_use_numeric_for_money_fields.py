"""use_numeric_for_money_fields

Revision ID: c4d5e6f7a8b9
Revises: b7c8d9e0f1a2
Create Date: 2026-03-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'c4d5e6f7a8b9'
down_revision: Union[str, Sequence[str], None] = 'b7c8d9e0f1a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _column_exists(inspector, table_name: str, column_name: str) -> bool:
    if not _table_exists(inspector, table_name):
        return False
    return any(col['name'] == column_name for col in inspector.get_columns(table_name))


def upgrade() -> None:
    bind = op.get_bind()
    # SQLite: column type changes via batch_alter_table fail due to FK constraints.
    # SQLite treats all numeric types identically at runtime, so skip on SQLite.
    if bind.dialect.name == "sqlite":
        return
    inspector = inspect(bind)

    money_type = sa.Numeric(12, 2)

    if _table_exists(inspector, 'products'):
        with op.batch_alter_table('products', schema=None) as batch_op:
            if _column_exists(inspector, 'products', 'price'):
                batch_op.alter_column('price', existing_type=sa.Float(), type_=money_type)
            if _column_exists(inspector, 'products', 'compare_price'):
                batch_op.alter_column('compare_price', existing_type=sa.Float(), type_=money_type)

    if _table_exists(inspector, 'orders'):
        with op.batch_alter_table('orders', schema=None) as batch_op:
            if _column_exists(inspector, 'orders', 'subtotal_amount'):
                batch_op.alter_column('subtotal_amount', existing_type=sa.Float(), type_=money_type)
            if _column_exists(inspector, 'orders', 'discount_amount'):
                batch_op.alter_column('discount_amount', existing_type=sa.Float(), type_=money_type)
            if _column_exists(inspector, 'orders', 'vat_amount'):
                batch_op.alter_column('vat_amount', existing_type=sa.Float(), type_=money_type)
            if _column_exists(inspector, 'orders', 'shipping_amount'):
                batch_op.alter_column('shipping_amount', existing_type=sa.Float(), type_=money_type)
            if _column_exists(inspector, 'orders', 'total_amount'):
                batch_op.alter_column('total_amount', existing_type=sa.Float(), type_=money_type)

    if _table_exists(inspector, 'order_items'):
        with op.batch_alter_table('order_items', schema=None) as batch_op:
            if _column_exists(inspector, 'order_items', 'price'):
                batch_op.alter_column('price', existing_type=sa.Float(), type_=money_type)

    if _table_exists(inspector, 'coupons'):
        with op.batch_alter_table('coupons', schema=None) as batch_op:
            if _column_exists(inspector, 'coupons', 'value'):
                batch_op.alter_column('value', existing_type=sa.Float(), type_=money_type)
            if _column_exists(inspector, 'coupons', 'min_order'):
                batch_op.alter_column('min_order', existing_type=sa.Float(), type_=money_type)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if _table_exists(inspector, 'coupons'):
        with op.batch_alter_table('coupons', schema=None) as batch_op:
            if _column_exists(inspector, 'coupons', 'min_order'):
                batch_op.alter_column('min_order', existing_type=sa.Numeric(12, 2), type_=sa.Float())
            if _column_exists(inspector, 'coupons', 'value'):
                batch_op.alter_column('value', existing_type=sa.Numeric(12, 2), type_=sa.Float())

    if _table_exists(inspector, 'order_items'):
        with op.batch_alter_table('order_items', schema=None) as batch_op:
            if _column_exists(inspector, 'order_items', 'price'):
                batch_op.alter_column('price', existing_type=sa.Numeric(12, 2), type_=sa.Float())

    if _table_exists(inspector, 'orders'):
        with op.batch_alter_table('orders', schema=None) as batch_op:
            if _column_exists(inspector, 'orders', 'total_amount'):
                batch_op.alter_column('total_amount', existing_type=sa.Numeric(12, 2), type_=sa.Float())
            if _column_exists(inspector, 'orders', 'shipping_amount'):
                batch_op.alter_column('shipping_amount', existing_type=sa.Numeric(12, 2), type_=sa.Float())
            if _column_exists(inspector, 'orders', 'vat_amount'):
                batch_op.alter_column('vat_amount', existing_type=sa.Numeric(12, 2), type_=sa.Float())
            if _column_exists(inspector, 'orders', 'discount_amount'):
                batch_op.alter_column('discount_amount', existing_type=sa.Numeric(12, 2), type_=sa.Float())
            if _column_exists(inspector, 'orders', 'subtotal_amount'):
                batch_op.alter_column('subtotal_amount', existing_type=sa.Numeric(12, 2), type_=sa.Float())

    if _table_exists(inspector, 'products'):
        with op.batch_alter_table('products', schema=None) as batch_op:
            if _column_exists(inspector, 'products', 'compare_price'):
                batch_op.alter_column('compare_price', existing_type=sa.Numeric(12, 2), type_=sa.Float())
            if _column_exists(inspector, 'products', 'price'):
                batch_op.alter_column('price', existing_type=sa.Numeric(12, 2), type_=sa.Float())

