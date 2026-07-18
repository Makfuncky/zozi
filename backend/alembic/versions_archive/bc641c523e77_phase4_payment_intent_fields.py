"""phase4_payment_intent_fields

Revision ID: bc641c523e77
Revises: 0b41557984a8
Create Date: 2026-03-02 23:30:30.617853

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'bc641c523e77'
down_revision: Union[str, Sequence[str], None] = '0b41557984a8'
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
        if 'payment_intent_id' not in existing_columns:
            batch_op.add_column(sa.Column('payment_intent_id', sa.String(), nullable=True))
        if 'paid_at' not in existing_columns:
            batch_op.add_column(sa.Column('paid_at', sa.DateTime(), nullable=True))
        if 'ix_orders_payment_intent_id' not in existing_indexes:
            batch_op.create_index(batch_op.f('ix_orders_payment_intent_id'), ['payment_intent_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = inspect(bind)
    if 'orders' not in inspector.get_table_names():
        return
    existing_columns = {column['name'] for column in inspector.get_columns('orders')}
    existing_indexes = {index['name'] for index in inspector.get_indexes('orders')}

    with op.batch_alter_table('orders', schema=None) as batch_op:
        if 'ix_orders_payment_intent_id' in existing_indexes:
            batch_op.drop_index(batch_op.f('ix_orders_payment_intent_id'))
        if 'paid_at' in existing_columns:
            batch_op.drop_column('paid_at')
        if 'payment_intent_id' in existing_columns:
            batch_op.drop_column('payment_intent_id')

