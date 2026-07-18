"""phase9_supplier_verification

Revision ID: 1abf0fe5acce
Revises: a1b2c3d4e5f6
Create Date: 2026-03-07 21:59:26.110641

SQLite runs this migration non-transactionally. Make index/column creation
idempotent so a partially applied run can recover cleanly.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = '1abf0fe5acce'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_names(inspector) -> set[str]:
    return set(inspector.get_table_names())


def _index_names(inspector, table_name: str) -> set[str]:
    if table_name not in _table_names(inspector):
        return set()
    return {index["name"] for index in inspector.get_indexes(table_name)}


def _column_names(inspector, table_name: str) -> set[str]:
    if table_name not in _table_names(inspector):
        return set()
    return {column["name"] for column in inspector.get_columns(table_name)}


def _create_index_if_missing(inspector, table_name: str, index_name: str, columns: list[str]) -> None:
    if table_name in _table_names(inspector) and index_name not in _index_names(inspector, table_name):
        op.create_index(index_name, table_name, columns, unique=False)


def _drop_index_if_present(inspector, table_name: str, index_name: str) -> None:
    if table_name in _table_names(inspector) and index_name in _index_names(inspector, table_name):
        op.drop_index(index_name, table_name=table_name)


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = inspect(bind)

    _create_index_if_missing(inspector, 'addresses', 'ix_addresses_id', ['id'])
    _create_index_if_missing(inspector, 'audit_logs', 'ix_audit_logs_action_created', ['action', 'created_at'])
    _create_index_if_missing(inspector, 'audit_logs', 'ix_audit_logs_user_created', ['user_id', 'created_at'])
    _create_index_if_missing(inspector, 'coupon_usages', 'ix_coupon_usages_id', ['id'])
    _create_index_if_missing(inspector, 'flash_sales', 'ix_flash_sales_id', ['id'])
    _create_index_if_missing(inspector, 'notifications', 'ix_notifications_user_created', ['user_id', 'created_at'])
    _create_index_if_missing(inspector, 'notifications', 'ix_notifications_user_read_created', ['user_id', 'read', 'created_at'])
    _create_index_if_missing(inspector, 'order_items', 'ix_order_items_order_product', ['order_id', 'product_id'])
    _create_index_if_missing(inspector, 'order_items', 'ix_order_items_product_order', ['product_id', 'order_id'])
    _create_index_if_missing(inspector, 'orders', 'ix_orders_status_created', ['status', 'created_at'])
    _create_index_if_missing(inspector, 'orders', 'ix_orders_user_created', ['user_id', 'created_at'])
    _create_index_if_missing(inspector, 'payouts', 'ix_payouts_supplier_created', ['supplier_id', 'created_at'])
    _create_index_if_missing(inspector, 'processed_webhook_events', 'ix_processed_webhook_events_id', ['id'])

    if 'products' in _table_names(inspector):
        with op.batch_alter_table('products', schema=None) as batch_op:
            batch_op.alter_column(
                'tags',
                existing_type=sa.TEXT(),
                type_=sa.String(),
                existing_nullable=True,
            )

    _create_index_if_missing(inspector, 'products', 'ix_products_brand_deleted', ['brand', 'is_deleted'])
    _create_index_if_missing(inspector, 'products', 'ix_products_category_deleted_created', ['category', 'is_deleted', 'created_at'])
    _create_index_if_missing(inspector, 'products', 'ix_products_supplier_deleted_created', ['supplier_id', 'is_deleted', 'created_at'])

    user_columns = _column_names(inspector, 'users')
    if 'users' in _table_names(inspector) and ({'is_verified', 'verification_note'} - user_columns):
        with op.batch_alter_table('users', schema=None) as batch_op:
            if 'is_verified' not in user_columns:
                batch_op.add_column(sa.Column('is_verified', sa.Boolean(), nullable=True))
            if 'verification_note' not in user_columns:
                batch_op.add_column(sa.Column('verification_note', sa.String(length=500), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = inspect(bind)

    user_columns = _column_names(inspector, 'users')
    if 'users' in _table_names(inspector) and ({'is_verified', 'verification_note'} & user_columns):
        with op.batch_alter_table('users', schema=None) as batch_op:
            if 'verification_note' in user_columns:
                batch_op.drop_column('verification_note')
            if 'is_verified' in user_columns:
                batch_op.drop_column('is_verified')

    if 'products' in _table_names(inspector):
        with op.batch_alter_table('products', schema=None) as batch_op:
            batch_op.alter_column(
                'tags',
                existing_type=sa.String(),
                type_=sa.TEXT(),
                existing_nullable=True,
            )

    _drop_index_if_present(inspector, 'products', 'ix_products_supplier_deleted_created')
    _drop_index_if_present(inspector, 'products', 'ix_products_category_deleted_created')
    _drop_index_if_present(inspector, 'products', 'ix_products_brand_deleted')
    _drop_index_if_present(inspector, 'processed_webhook_events', 'ix_processed_webhook_events_id')
    _drop_index_if_present(inspector, 'payouts', 'ix_payouts_supplier_created')
    _drop_index_if_present(inspector, 'orders', 'ix_orders_user_created')
    _drop_index_if_present(inspector, 'orders', 'ix_orders_status_created')
    _drop_index_if_present(inspector, 'order_items', 'ix_order_items_product_order')
    _drop_index_if_present(inspector, 'order_items', 'ix_order_items_order_product')
    _drop_index_if_present(inspector, 'notifications', 'ix_notifications_user_read_created')
    _drop_index_if_present(inspector, 'notifications', 'ix_notifications_user_created')
    _drop_index_if_present(inspector, 'flash_sales', 'ix_flash_sales_id')
    _drop_index_if_present(inspector, 'coupon_usages', 'ix_coupon_usages_id')
    _drop_index_if_present(inspector, 'audit_logs', 'ix_audit_logs_user_created')
    _drop_index_if_present(inspector, 'audit_logs', 'ix_audit_logs_action_created')
    _drop_index_if_present(inspector, 'addresses', 'ix_addresses_id')

