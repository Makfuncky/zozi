"""baseline_canonical_orm_schema_clean

Revision ID: b81bfc888610
Revises: 
Create Date: 2026-07-26 16:09:14.215676+00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b81bfc888610'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Baseline migration — captures the delta between the current ORM schema
    # and what's already in the database. Only adds genuinely missing objects.
    # Columns added previously by ``Base.metadata.create_all()`` are skipped.

    op.add_column('internal_messages', sa.Column('is_deleted', sa.Boolean(), nullable=True))
    op.add_column('org_units', sa.Column('path', sa.String(length=500), nullable=True, comment="Materialized path like '/1/12/45/'"))
    op.add_column('org_units', sa.Column('depth', sa.Integer(), nullable=True, comment='Depth in hierarchy (0 = root)'))
    op.create_index('ix_org_unit_parent', 'org_units', ['parent_id'], unique=False)
    op.create_index('ix_org_unit_path', 'org_units', ['path'], unique=False)
    op.create_index(op.f('ix_sales_order_lines_id'), 'sales_order_lines', ['id'], unique=False)
    op.create_index(op.f('ix_sales_order_lines_so_id'), 'sales_order_lines', ['so_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_sales_order_lines_so_id'), table_name='sales_order_lines')
    op.drop_index(op.f('ix_sales_order_lines_id'), table_name='sales_order_lines')
    op.drop_index('ix_org_unit_path', table_name='org_units')
    op.drop_index('ix_org_unit_parent', table_name='org_units')
    op.drop_column('org_units', 'depth')
    op.drop_column('org_units', 'path')
    op.drop_column('internal_messages', 'is_deleted')
