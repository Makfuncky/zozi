"""add_compare_price_to_products

Revision ID: 18afc076b757
Revises: 48c2a8404b0e
Create Date: 2026-03-15 01:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = '18afc076b757'
down_revision: Union[str, Sequence[str], None] = '48c2a8404b0e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(inspector, table: str, column: str) -> bool:
    cols = {c["name"] for c in inspector.get_columns(table)}
    return column in cols


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if not _column_exists(inspector, 'products', 'compare_price'):
        with op.batch_alter_table('products', schema=None) as batch_op:
            batch_op.add_column(sa.Column('compare_price', sa.Float(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if _column_exists(inspector, 'products', 'compare_price'):
        with op.batch_alter_table('products', schema=None) as batch_op:
            batch_op.drop_column('compare_price')

