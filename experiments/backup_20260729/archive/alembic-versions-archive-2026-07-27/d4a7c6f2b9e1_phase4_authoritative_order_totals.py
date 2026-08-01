"""phase4_authoritative_order_totals

Revision ID: d4a7c6f2b9e1
Revises: bc641c523e77
Create Date: 2026-03-07 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'd4a7c6f2b9e1'
down_revision: Union[str, Sequence[str], None] = 'bc641c523e77'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = inspect(bind)
    if 'orders' not in inspector.get_table_names():
        return
    existing_columns = {column['name'] for column in inspector.get_columns('orders')}
    existing_indexes = {index['name'] for index in inspector.get_indexes('orders')}

    with op.batch_alter_table('orders', schema=None) as batch_op:
        if 'subtotal_amount' not in existing_columns:
            batch_op.add_column(sa.Column('subtotal_amount', sa.Float(), nullable=True))
        if 'discount_amount' not in existing_columns:
            batch_op.add_column(sa.Column('discount_amount', sa.Float(), nullable=True, server_default='0'))
        if 'coupon_code' not in existing_columns:
            batch_op.add_column(sa.Column('coupon_code', sa.String(), nullable=True))
        if 'ix_orders_coupon_code' not in existing_indexes:
            batch_op.create_index(batch_op.f('ix_orders_coupon_code'), ['coupon_code'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = inspect(bind)
    if 'orders' not in inspector.get_table_names():
        return
    existing_columns = {column['name'] for column in inspector.get_columns('orders')}
    existing_indexes = {index['name'] for index in inspector.get_indexes('orders')}

    with op.batch_alter_table('orders', schema=None) as batch_op:
        if 'ix_orders_coupon_code' in existing_indexes:
            batch_op.drop_index(batch_op.f('ix_orders_coupon_code'))
        if 'coupon_code' in existing_columns:
            batch_op.drop_column('coupon_code')
        if 'discount_amount' in existing_columns:
            batch_op.drop_column('discount_amount')
        if 'subtotal_amount' in existing_columns:
            batch_op.drop_column('subtotal_amount')

