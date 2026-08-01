"""add_maximum_charge_to_logistics_pricing_profiles

Revision ID: ab8d4b3ead2b
Revises: zb1c2d3e4f5
Create Date: 2026-04-10 20:49:20.749129

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ab8d4b3ead2b'
down_revision: Union[str, Sequence[str], None] = 'zb1c2d3e4f5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add maximum_charge guardrail column to logistics_pricing_profiles."""
    with op.batch_alter_table('logistics_pricing_profiles', schema=None) as batch_op:
        batch_op.add_column(sa.Column('maximum_charge', sa.Numeric(precision=12, scale=2), nullable=True))


def downgrade() -> None:
    """Remove maximum_charge column from logistics_pricing_profiles."""
    with op.batch_alter_table('logistics_pricing_profiles', schema=None) as batch_op:
        batch_op.drop_column('maximum_charge')

