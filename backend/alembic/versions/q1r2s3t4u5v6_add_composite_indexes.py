"""Add composite indexes for high-traffic query paths

Revision ID: q1r2s3t4u5v6
Revises: 20915daf9b29
Create Date: 2026-06-25 01:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'q1r2s3t4u5v6'
down_revision = '20915daf9b29'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index('ix_orders_user_created', 'orders', ['user_id', 'created_at'])
    op.create_index('ix_orders_status_created', 'orders', ['status', 'created_at'])
    op.create_index('ix_products_category_deleted', 'products', ['category', 'is_deleted'])
    op.create_index('ix_products_brand_deleted', 'products', ['brand', 'is_deleted'])
    op.create_index('ix_product_variants_product_active', 'product_variants', ['product_id', 'is_active'])
    op.create_index('ix_order_items_product_order', 'order_items', ['product_id', 'order_id'])
    op.create_index('ix_reviews_product_rating', 'reviews', ['product_id', 'rating'])
    op.create_index('ix_user_devices_user_fp', 'user_devices', ['user_id', 'fingerprint_hash'])
    op.create_index('ix_wishlists_user_product', 'wishlists', ['user_id', 'product_id'])
    op.create_index('ix_cart_items_user_updated', 'cart_items', ['user_id', 'updated_at'])


def downgrade():
    op.drop_index('ix_cart_items_user_updated', table_name='cart_items')
    op.drop_index('ix_wishlists_user_product', table_name='wishlists')
    op.drop_index('ix_user_devices_user_fp', table_name='user_devices')
    op.drop_index('ix_reviews_product_rating', table_name='reviews')
    op.drop_index('ix_order_items_product_order', table_name='order_items')
    op.drop_index('ix_product_variants_product_active', table_name='product_variants')
    op.drop_index('ix_products_brand_deleted', table_name='products')
    op.drop_index('ix_products_category_deleted', table_name='products')
    op.drop_index('ix_orders_status_created', table_name='orders')
    op.drop_index('ix_orders_user_created', table_name='orders')

