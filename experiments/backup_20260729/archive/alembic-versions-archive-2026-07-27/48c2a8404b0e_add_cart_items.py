"""add_cart_items

Revision ID: 48c2a8404b0e
Revises: 1abf0fe5acce
Create Date: 2026-03-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = '48c2a8404b0e'
down_revision: Union[str, Sequence[str], None] = '1abf0fe5acce'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = set(inspector.get_table_names())

    if "cart_items" not in tables:
        op.create_table(
            'cart_items',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
            sa.Column('product_id', sa.Integer(), sa.ForeignKey('products.id'), nullable=True),
            sa.Column('quantity', sa.Integer(), nullable=False, server_default='1'),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('user_id', 'product_id', name='uq_cart_user_product'),
        )
        op.create_index('ix_cart_items_id', 'cart_items', ['id'])
        op.create_index('ix_cart_items_user_id', 'cart_items', ['user_id'])
        op.create_index('ix_cart_items_product_id', 'cart_items', ['product_id'])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = set(inspector.get_table_names())

    if "cart_items" in tables:
        op.drop_table('cart_items')

