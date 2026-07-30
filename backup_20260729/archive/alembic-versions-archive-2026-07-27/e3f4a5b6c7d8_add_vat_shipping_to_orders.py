"""add_vat_shipping_to_orders

Revision ID: e3f4a5b6c7d8
Revises: d1e2f3a4b5c6
Create Date: 2026-03-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = 'e3f4a5b6c7d8'
down_revision: Union[str, Sequence[str], None] = 'd1e2f3a4b5c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(inspector, table: str, column: str) -> bool:
    cols = {c["name"] for c in inspector.get_columns(table)}
    return column in cols


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    cols = {c["name"] for c in inspector.get_columns("orders")}
    with op.batch_alter_table('orders', schema=None) as batch_op:
        if 'vat_amount' not in cols:
            batch_op.add_column(sa.Column('vat_amount', sa.Float(), nullable=True, server_default='0'))
        if 'shipping_amount' not in cols:
            batch_op.add_column(sa.Column('shipping_amount', sa.Float(), nullable=True, server_default='0'))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    cols = {c["name"] for c in inspector.get_columns("orders")}
    with op.batch_alter_table('orders', schema=None) as batch_op:
        if 'shipping_amount' in cols:
            batch_op.drop_column('shipping_amount')
        if 'vat_amount' in cols:
            batch_op.drop_column('vat_amount')

