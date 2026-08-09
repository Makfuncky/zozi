"""add_order_logistics_allocations

Revision ID: 5d9f3a1c2b44
Revises: 784a891dd168
Create Date: 2026-04-03 18:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5d9f3a1c2b44'
down_revision: Union[str, Sequence[str], None] = '784a891dd168'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'order_logistics_allocations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('supplier_id', sa.Integer(), nullable=False),
        sa.Column('partner_id', sa.Integer(), nullable=True),
        sa.Column('service_area_id', sa.Integer(), nullable=True),
        sa.Column('shipment_id', sa.Integer(), nullable=True),
        sa.Column('allocation_source', sa.String(length=40), nullable=False),
        sa.Column('partner_name_snapshot', sa.String(length=200), nullable=True),
        sa.Column('partner_code_snapshot', sa.String(length=50), nullable=True),
        sa.Column('service_area_label_snapshot', sa.String(length=120), nullable=True),
        sa.Column('destination_country', sa.String(length=120), nullable=True),
        sa.Column('destination_city', sa.String(length=120), nullable=True),
        sa.Column('shipping_amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('pickup_charge', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('dropoff_charge', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('estimated_delivery_min', sa.Integer(), nullable=True),
        sa.Column('estimated_delivery_max', sa.Integer(), nullable=True),
        sa.Column('currency', sa.String(length=10), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.CheckConstraint('dropoff_charge >= 0', name='ck_order_logistics_allocations_dropoff_nonnegative'),
        sa.CheckConstraint('pickup_charge >= 0', name='ck_order_logistics_allocations_pickup_nonnegative'),
        sa.CheckConstraint('shipping_amount >= 0', name='ck_order_logistics_allocations_shipping_nonnegative'),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id']),
        sa.ForeignKeyConstraint(['partner_id'], ['logistics_partners.id']),
        sa.ForeignKeyConstraint(['service_area_id'], ['logistics_partner_service_areas.id']),
        sa.ForeignKeyConstraint(['shipment_id'], ['shipments.id']),
        sa.ForeignKeyConstraint(['supplier_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('order_id', 'supplier_id', name='uq_order_logistics_allocations_order_supplier'),
    )
    with op.batch_alter_table('order_logistics_allocations', schema=None) as batch_op:
        batch_op.create_index('ix_order_logistics_allocations_order', ['order_id'], unique=False)
        batch_op.create_index('ix_order_logistics_allocations_partner', ['partner_id'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('order_logistics_allocations', schema=None) as batch_op:
        batch_op.drop_index('ix_order_logistics_allocations_partner')
        batch_op.drop_index('ix_order_logistics_allocations_order')

    op.drop_table('order_logistics_allocations')

