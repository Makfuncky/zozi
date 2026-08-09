"""phase0_product_active_sales_count

Add is_active and sales_count columns to the products table.
- is_active  (Boolean, default True)  — lets suppliers deactivate a listing without deleting it
- sales_count (Integer, default 0)   — incremented each time an order containing this product
                                       is confirmed; used by supplier analytics dashboard

Revision ID: f2c3d4e5f6a7
Revises: d4a7c6f2b9e1
Create Date: 2026-03-07 00:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'f2c3d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = 'd4a7c6f2b9e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add is_active and sales_count to products (idempotent)."""
    bind = op.get_bind()
    inspector = inspect(bind)
    if 'products' not in inspector.get_table_names():
        return

    existing_columns = {col['name'] for col in inspector.get_columns('products')}

    with op.batch_alter_table('products', schema=None) as batch_op:
        if 'is_active' not in existing_columns:
            batch_op.add_column(
                sa.Column('is_active', sa.Boolean(), nullable=True, server_default=sa.true())
            )
        if 'sales_count' not in existing_columns:
            batch_op.add_column(
                sa.Column('sales_count', sa.Integer(), nullable=True, server_default=sa.text('0'))
            )


def downgrade() -> None:
    """Remove is_active and sales_count from products (idempotent)."""
    bind = op.get_bind()
    inspector = inspect(bind)
    if 'products' not in inspector.get_table_names():
        return

    existing_columns = {col['name'] for col in inspector.get_columns('products')}

    with op.batch_alter_table('products', schema=None) as batch_op:
        if 'sales_count' in existing_columns:
            batch_op.drop_column('sales_count')
        if 'is_active' in existing_columns:
            batch_op.drop_column('is_active')

