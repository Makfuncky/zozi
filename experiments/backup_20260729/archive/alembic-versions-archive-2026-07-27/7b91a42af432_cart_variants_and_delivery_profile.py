"""cart_variants_and_delivery_profile

Revision ID: 7b91a42af432
Revises: 18afc076b757
Create Date: 2026-03-17 10:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7b91a42af432'
down_revision: Union[str, Sequence[str], None] = '18afc076b757'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('cart_items', schema=None) as batch_op:
        batch_op.add_column(sa.Column('selected_size', sa.String(length=100), server_default='', nullable=False))
        batch_op.add_column(sa.Column('selected_color', sa.String(length=100), server_default='', nullable=False))
        batch_op.drop_constraint('uq_cart_user_product', type_='unique')
        batch_op.create_unique_constraint('uq_cart_user_product_variant', ['user_id', 'product_id', 'selected_size', 'selected_color'])

    with op.batch_alter_table('order_items', schema=None) as batch_op:
        batch_op.add_column(sa.Column('selected_size', sa.String(length=100), server_default='', nullable=False))
        batch_op.add_column(sa.Column('selected_color', sa.String(length=100), server_default='', nullable=False))

    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.add_column(sa.Column('customer_phone', sa.String(length=30), nullable=True))
        batch_op.add_column(sa.Column('delivery_location', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('delivery_note', sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.drop_column('delivery_note')
        batch_op.drop_column('delivery_location')
        batch_op.drop_column('customer_phone')

    with op.batch_alter_table('order_items', schema=None) as batch_op:
        batch_op.drop_column('selected_color')
        batch_op.drop_column('selected_size')

    with op.batch_alter_table('cart_items', schema=None) as batch_op:
        batch_op.drop_constraint('uq_cart_user_product_variant', type_='unique')
        batch_op.create_unique_constraint('uq_cart_user_product', ['user_id', 'product_id'])
        batch_op.drop_column('selected_color')
        batch_op.drop_column('selected_size')

