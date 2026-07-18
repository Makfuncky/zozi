"""add_operating_regions_to_supplier_

Revision ID: 97126a91bc8e
Revises: c9d2e3f4a5b6
Create Date: 2026-03-17 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = '97126a91bc8e'
down_revision: Union[str, Sequence[str], None] = 'c9d2e3f4a5b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(inspector, table: str, column: str) -> bool:
    cols = {c["name"] for c in inspector.get_columns(table)}
    return column in cols


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if not _column_exists(inspector, 'supplier_profiles', 'operating_regions'):
        with op.batch_alter_table('supplier_profiles', schema=None) as batch_op:
            batch_op.add_column(sa.Column('operating_regions', sa.Text(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if _column_exists(inspector, 'supplier_profiles', 'operating_regions'):
        with op.batch_alter_table('supplier_profiles', schema=None) as batch_op:
            batch_op.drop_column('operating_regions')

