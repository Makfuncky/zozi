"""add_partner_tracking_and_charge_split

Revision ID: 784a891dd168
Revises: 79b533c27897
Create Date: 2026-04-03 01:07:32.629535

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '784a891dd168'
down_revision: Union[str, Sequence[str], None] = '79b533c27897'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Orders: track which logistics partner/service area was used at checkout
    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.add_column(sa.Column('selected_partner_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('selected_service_area_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('estimated_delivery_min', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('estimated_delivery_max', sa.Integer(), nullable=True))

    # Service areas: optional pickup/dropoff charge split
    with op.batch_alter_table('logistics_partner_service_areas', schema=None) as batch_op:
        batch_op.add_column(sa.Column('pickup_charge', sa.Numeric(precision=12, scale=2), nullable=True))
        batch_op.add_column(sa.Column('dropoff_charge', sa.Numeric(precision=12, scale=2), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('logistics_partner_service_areas', schema=None) as batch_op:
        batch_op.drop_column('dropoff_charge')
        batch_op.drop_column('pickup_charge')

    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.drop_column('estimated_delivery_max')
        batch_op.drop_column('estimated_delivery_min')
        batch_op.drop_column('selected_service_area_id')
        batch_op.drop_column('selected_partner_id')

