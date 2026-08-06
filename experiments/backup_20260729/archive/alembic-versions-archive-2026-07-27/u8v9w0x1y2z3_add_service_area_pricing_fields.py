"""add_service_area_pricing_fields

Revision ID: u8v9w0x1y2z3
Revises: t2u3v4w5x6y7
Create Date: 2026-04-08 15:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'u8v9w0x1y2z3'
down_revision: Union[str, Sequence[str], None] = 't2u3v4w5x6y7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('logistics_partner_service_areas', schema=None) as batch_op:
        batch_op.add_column(sa.Column('minimum_charge', sa.Numeric(precision=12, scale=2), nullable=True))
        batch_op.add_column(sa.Column('per_kg_rate', sa.Numeric(precision=12, scale=2), nullable=True))
        batch_op.add_column(sa.Column('fuel_multiplier', sa.Numeric(precision=8, scale=4), nullable=True))
        batch_op.create_check_constraint(
            'ck_lp_service_areas_minimum_charge_nonnegative',
            'minimum_charge IS NULL OR minimum_charge >= 0',
        )
        batch_op.create_check_constraint(
            'ck_lp_service_areas_per_kg_nonnegative',
            'per_kg_rate IS NULL OR per_kg_rate >= 0',
        )
        batch_op.create_check_constraint(
            'ck_lp_service_areas_fuel_multiplier_positive',
            'fuel_multiplier IS NULL OR fuel_multiplier > 0',
        )


def downgrade() -> None:
    with op.batch_alter_table('logistics_partner_service_areas', schema=None) as batch_op:
        batch_op.drop_constraint('ck_lp_service_areas_fuel_multiplier_positive', type_='check')
        batch_op.drop_constraint('ck_lp_service_areas_per_kg_nonnegative', type_='check')
        batch_op.drop_constraint('ck_lp_service_areas_minimum_charge_nonnegative', type_='check')
        batch_op.drop_column('fuel_multiplier')
        batch_op.drop_column('per_kg_rate')
        batch_op.drop_column('minimum_charge')

