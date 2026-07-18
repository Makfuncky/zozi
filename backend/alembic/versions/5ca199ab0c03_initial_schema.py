"""initial_schema

Revision ID: 5ca199ab0c03
Revises: 
Create Date: 2026-03-02 22:40:17.281556

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5ca199ab0c03'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('username', sa.String(), nullable=True),
        sa.Column('hashed_password', sa.String(), nullable=True),
        sa.Column('role', sa.String(), nullable=True, server_default='customer'),
        sa.Column('is_active', sa.Integer(), nullable=True, server_default='1'),
        sa.Column('phone', sa.String(), nullable=True),
        sa.Column('profile_image', sa.String(), nullable=True),
        sa.Column('address_book', sa.Text(), nullable=True),
        sa.Column('preferred_language', sa.String(), nullable=True, server_default='en'),
        sa.Column('email_verified', sa.Boolean(), nullable=True, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_users_id', 'users', ['id'], unique=False)
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_username', 'users', ['username'], unique=True)
    op.create_index('ix_users_role', 'users', ['role'], unique=False)

    op.create_table(
        'categories',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('slug', sa.String(), nullable=True),
        sa.Column('icon', sa.String(), nullable=True),
        sa.Column('image_url', sa.String(), nullable=True),
        sa.Column('parent_id', sa.Integer(), sa.ForeignKey('categories.id'), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_categories_id', 'categories', ['id'], unique=False)
    op.create_index('ix_categories_name', 'categories', ['name'], unique=False)
    op.create_index('ix_categories_slug', 'categories', ['slug'], unique=True)

    op.create_table(
        'products',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('price', sa.Float(), nullable=True),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('brand', sa.String(), nullable=True),
        sa.Column('rating', sa.Float(), nullable=True, server_default='0'),
        sa.Column('image_url', sa.String(), nullable=True),
        sa.Column('stock', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('color', sa.String(), nullable=True),
        sa.Column('tags', sa.String(), nullable=True),
        sa.Column('ai_description', sa.Text(), nullable=True),
        sa.Column('sizes', sa.Text(), nullable=True),
        sa.Column('materials', sa.String(), nullable=True),
        sa.Column('additional_images', sa.Text(), nullable=True),
        sa.Column('weight', sa.Float(), nullable=True),
        sa.Column('dimensions', sa.String(), nullable=True),
        sa.Column('supplier_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=True, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_products_id', 'products', ['id'], unique=False)
    op.create_index('ix_products_name', 'products', ['name'], unique=False)
    op.create_index('ix_products_category', 'products', ['category'], unique=False)
    op.create_index('ix_products_brand', 'products', ['brand'], unique=False)
    op.create_index('ix_products_color', 'products', ['color'], unique=False)
    op.create_index('ix_products_supplier_deleted_created', 'products', ['supplier_id', 'is_deleted', 'created_at'], unique=False)
    op.create_index('ix_products_category_deleted_created', 'products', ['category', 'is_deleted', 'created_at'], unique=False)
    op.create_index('ix_products_brand_deleted', 'products', ['brand', 'is_deleted'], unique=False)

    op.create_table(
        'coupons',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('discount_type', sa.String(), nullable=True, server_default='percent'),
        sa.Column('value', sa.Float(), nullable=True),
        sa.Column('min_order', sa.Float(), nullable=True, server_default='0'),
        sa.Column('max_uses', sa.Integer(), nullable=True),
        sa.Column('uses_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_coupons_id', 'coupons', ['id'], unique=False)
    op.create_index('ix_coupons_code', 'coupons', ['code'], unique=True)

    op.create_table(
        'orders',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('subtotal_amount', sa.Float(), nullable=True),
        sa.Column('discount_amount', sa.Float(), nullable=True, server_default='0'),
        sa.Column('total_amount', sa.Float(), nullable=True),
        sa.Column('coupon_code', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=True, server_default='pending'),
        sa.Column('shipping_address', sa.Text(), nullable=True),
        sa.Column('tracking_number', sa.String(), nullable=True),
        sa.Column('payment_intent_id', sa.String(), nullable=True),
        sa.Column('paid_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_orders_id', 'orders', ['id'], unique=False)
    op.create_index('ix_orders_user_id', 'orders', ['user_id'], unique=False)
    op.create_index('ix_orders_coupon_code', 'orders', ['coupon_code'], unique=False)
    op.create_index('ix_orders_status', 'orders', ['status'], unique=False)
    op.create_index('ix_orders_payment_intent_id', 'orders', ['payment_intent_id'], unique=False)
    op.create_index('ix_orders_user_created', 'orders', ['user_id', 'created_at'], unique=False)
    op.create_index('ix_orders_status_created', 'orders', ['status', 'created_at'], unique=False)

    op.create_table(
        'order_items',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('order_id', sa.Integer(), sa.ForeignKey('orders.id'), nullable=True),
        sa.Column('product_id', sa.Integer(), sa.ForeignKey('products.id'), nullable=True),
        sa.Column('quantity', sa.Integer(), nullable=True),
        sa.Column('price', sa.Float(), nullable=True),
    )
    op.create_index('ix_order_items_id', 'order_items', ['id'], unique=False)
    op.create_index('ix_order_items_order_id', 'order_items', ['order_id'], unique=False)
    op.create_index('ix_order_items_product_id', 'order_items', ['product_id'], unique=False)
    op.create_index('ix_order_items_product_order', 'order_items', ['product_id', 'order_id'], unique=False)
    op.create_index('ix_order_items_order_product', 'order_items', ['order_id', 'product_id'], unique=False)

    op.create_table(
        'reviews',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('product_id', sa.Integer(), sa.ForeignKey('products.id'), nullable=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('rating', sa.Float(), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('image_url', sa.String(), nullable=True),
        sa.Column('is_verified_purchase', sa.Boolean(), nullable=True, server_default=sa.false()),
        sa.Column('is_deleted', sa.Boolean(), nullable=True, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_reviews_id', 'reviews', ['id'], unique=False)
    op.create_index('ix_reviews_product_id', 'reviews', ['product_id'], unique=False)
    op.create_index('ix_reviews_user_id', 'reviews', ['user_id'], unique=False)

    op.create_table(
        'wishlists',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('product_id', sa.Integer(), sa.ForeignKey('products.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_wishlists_id', 'wishlists', ['id'], unique=False)
    op.create_index('ix_wishlists_user_id', 'wishlists', ['user_id'], unique=False)
    op.create_index('ix_wishlists_product_id', 'wishlists', ['product_id'], unique=False)

    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('type', sa.String(), nullable=True),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('read', sa.Boolean(), nullable=True, server_default=sa.false()),
        sa.Column('link', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_notifications_id', 'notifications', ['id'], unique=False)
    op.create_index('ix_notifications_user_id', 'notifications', ['user_id'], unique=False)
    op.create_index('ix_notifications_user_created', 'notifications', ['user_id', 'created_at'], unique=False)
    op.create_index('ix_notifications_user_read_created', 'notifications', ['user_id', 'read', 'created_at'], unique=False)

    op.create_table(
        'password_reset_tokens',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('token', sa.String(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('used', sa.Boolean(), nullable=True, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_password_reset_tokens_id', 'password_reset_tokens', ['id'], unique=False)
    op.create_index('ix_password_reset_tokens_user_id', 'password_reset_tokens', ['user_id'], unique=False)
    op.create_index('ix_password_reset_tokens_token', 'password_reset_tokens', ['token'], unique=True)

    op.create_table(
        'email_verification_tokens',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('token', sa.String(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('used', sa.Boolean(), nullable=True, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_email_verification_tokens_id', 'email_verification_tokens', ['id'], unique=False)
    op.create_index('ix_email_verification_tokens_user_id', 'email_verification_tokens', ['user_id'], unique=False)
    op.create_index('ix_email_verification_tokens_token', 'email_verification_tokens', ['token'], unique=True)

    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('username', sa.String(), nullable=True),
        sa.Column('user_role', sa.String(), nullable=True),
        sa.Column('action', sa.String(), nullable=True),
        sa.Column('resource_type', sa.String(), nullable=True),
        sa.Column('resource_id', sa.String(), nullable=True),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('user_agent', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=True, server_default='success'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_audit_logs_id', 'audit_logs', ['id'], unique=False)
    op.create_index('ix_audit_logs_user_id', 'audit_logs', ['user_id'], unique=False)
    op.create_index('ix_audit_logs_action', 'audit_logs', ['action'], unique=False)
    op.create_index('ix_audit_logs_resource_type', 'audit_logs', ['resource_type'], unique=False)
    op.create_index('ix_audit_logs_ip_address', 'audit_logs', ['ip_address'], unique=False)
    op.create_index('ix_audit_logs_created_at', 'audit_logs', ['created_at'], unique=False)
    op.create_index('ix_audit_logs_action_created', 'audit_logs', ['action', 'created_at'], unique=False)
    op.create_index('ix_audit_logs_user_created', 'audit_logs', ['user_id', 'created_at'], unique=False)

    op.create_table(
        'payouts',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('supplier_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('status', sa.String(), nullable=True, server_default='pending'),
        sa.Column('method', sa.String(), nullable=True, server_default='bank'),
        sa.Column('reference', sa.String(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_payouts_id', 'payouts', ['id'], unique=False)
    op.create_index('ix_payouts_supplier_id', 'payouts', ['supplier_id'], unique=False)
    op.create_index('ix_payouts_supplier_created', 'payouts', ['supplier_id', 'created_at'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_payouts_supplier_created', table_name='payouts')
    op.drop_index('ix_payouts_supplier_id', table_name='payouts')
    op.drop_index('ix_payouts_id', table_name='payouts')
    op.drop_table('payouts')

    op.drop_index('ix_audit_logs_user_created', table_name='audit_logs')
    op.drop_index('ix_audit_logs_action_created', table_name='audit_logs')
    op.drop_index('ix_audit_logs_created_at', table_name='audit_logs')
    op.drop_index('ix_audit_logs_ip_address', table_name='audit_logs')
    op.drop_index('ix_audit_logs_resource_type', table_name='audit_logs')
    op.drop_index('ix_audit_logs_action', table_name='audit_logs')
    op.drop_index('ix_audit_logs_user_id', table_name='audit_logs')
    op.drop_index('ix_audit_logs_id', table_name='audit_logs')
    op.drop_table('audit_logs')

    op.drop_index('ix_email_verification_tokens_token', table_name='email_verification_tokens')
    op.drop_index('ix_email_verification_tokens_user_id', table_name='email_verification_tokens')
    op.drop_index('ix_email_verification_tokens_id', table_name='email_verification_tokens')
    op.drop_table('email_verification_tokens')

    op.drop_index('ix_password_reset_tokens_token', table_name='password_reset_tokens')
    op.drop_index('ix_password_reset_tokens_user_id', table_name='password_reset_tokens')
    op.drop_index('ix_password_reset_tokens_id', table_name='password_reset_tokens')
    op.drop_table('password_reset_tokens')

    op.drop_index('ix_notifications_user_read_created', table_name='notifications')
    op.drop_index('ix_notifications_user_created', table_name='notifications')
    op.drop_index('ix_notifications_user_id', table_name='notifications')
    op.drop_index('ix_notifications_id', table_name='notifications')
    op.drop_table('notifications')

    op.drop_index('ix_wishlists_product_id', table_name='wishlists')
    op.drop_index('ix_wishlists_user_id', table_name='wishlists')
    op.drop_index('ix_wishlists_id', table_name='wishlists')
    op.drop_table('wishlists')

    op.drop_index('ix_reviews_user_id', table_name='reviews')
    op.drop_index('ix_reviews_product_id', table_name='reviews')
    op.drop_index('ix_reviews_id', table_name='reviews')
    op.drop_table('reviews')

    op.drop_index('ix_order_items_order_product', table_name='order_items')
    op.drop_index('ix_order_items_product_order', table_name='order_items')
    op.drop_index('ix_order_items_product_id', table_name='order_items')
    op.drop_index('ix_order_items_order_id', table_name='order_items')
    op.drop_index('ix_order_items_id', table_name='order_items')
    op.drop_table('order_items')

    op.drop_index('ix_orders_status_created', table_name='orders')
    op.drop_index('ix_orders_user_created', table_name='orders')
    op.drop_index('ix_orders_payment_intent_id', table_name='orders')
    op.drop_index('ix_orders_status', table_name='orders')
    op.drop_index('ix_orders_coupon_code', table_name='orders')
    op.drop_index('ix_orders_user_id', table_name='orders')
    op.drop_index('ix_orders_id', table_name='orders')
    op.drop_table('orders')

    op.drop_index('ix_coupons_code', table_name='coupons')
    op.drop_index('ix_coupons_id', table_name='coupons')
    op.drop_table('coupons')

    op.drop_index('ix_products_brand_deleted', table_name='products')
    op.drop_index('ix_products_category_deleted_created', table_name='products')
    op.drop_index('ix_products_supplier_deleted_created', table_name='products')
    op.drop_index('ix_products_color', table_name='products')
    op.drop_index('ix_products_brand', table_name='products')
    op.drop_index('ix_products_category', table_name='products')
    op.drop_index('ix_products_name', table_name='products')
    op.drop_index('ix_products_id', table_name='products')
    op.drop_table('products')

    op.drop_index('ix_categories_slug', table_name='categories')
    op.drop_index('ix_categories_name', table_name='categories')
    op.drop_index('ix_categories_id', table_name='categories')
    op.drop_table('categories')

    op.drop_index('ix_users_role', table_name='users')
    op.drop_index('ix_users_username', table_name='users')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_index('ix_users_id', table_name='users')
    op.drop_table('users')

