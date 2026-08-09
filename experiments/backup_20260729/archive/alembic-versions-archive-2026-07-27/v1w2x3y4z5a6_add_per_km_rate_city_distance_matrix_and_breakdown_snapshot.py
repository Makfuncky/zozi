"""add_per_km_rate_city_distance_matrix_and_breakdown_snapshot

Revision ID: v1w2x3y4z5a6
Revises: u8v9w0x1y2z3
Create Date: 2026-04-09 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'v1w2x3y4z5a6'
down_revision: Union[str, Sequence[str], None] = 'u8v9w0x1y2z3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add per_km_rate column to logistics_partner_service_areas
    with op.batch_alter_table('logistics_partner_service_areas', schema=None) as batch_op:
        batch_op.add_column(sa.Column('per_km_rate', sa.Numeric(precision=12, scale=4), nullable=True))
        batch_op.create_check_constraint(
            'ck_lp_service_areas_per_km_nonnegative',
            'per_km_rate IS NULL OR per_km_rate >= 0',
        )

    # 2. Add pricing_breakdown_json column to order_logistics_allocations
    with op.batch_alter_table('order_logistics_allocations', schema=None) as batch_op:
        batch_op.add_column(sa.Column('pricing_breakdown_json', sa.Text(), nullable=True))

    # 3. Create city_distance_matrix table
    op.create_table(
        'city_distance_matrix',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('origin_country_code', sa.String(length=10), nullable=False),
        sa.Column('origin_city_name', sa.String(length=120), nullable=False),
        sa.Column('destination_country_code', sa.String(length=10), nullable=False),
        sa.Column('destination_city_name', sa.String(length=120), nullable=False),
        sa.Column('distance_km', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('updated_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'origin_country_code',
            'origin_city_name',
            'destination_country_code',
            'destination_city_name',
            name='uq_city_distance_matrix_route',
        ),
        sa.CheckConstraint('distance_km > 0', name='ck_city_distance_km_positive'),
    )
    op.create_index('ix_city_distance_matrix_id', 'city_distance_matrix', ['id'], unique=False)
    op.create_index('ix_city_distance_matrix_origin', 'city_distance_matrix', ['origin_country_code', 'origin_city_name'], unique=False)
    op.create_index('ix_city_distance_matrix_dest', 'city_distance_matrix', ['destination_country_code', 'destination_city_name'], unique=False)


def downgrade() -> None:
    # 3. Drop city_distance_matrix table
    op.drop_index('ix_city_distance_matrix_dest', table_name='city_distance_matrix')
    op.drop_index('ix_city_distance_matrix_origin', table_name='city_distance_matrix')
    op.drop_index('ix_city_distance_matrix_id', table_name='city_distance_matrix')
    op.drop_table('city_distance_matrix')

    # 2. Remove pricing_breakdown_json column
    with op.batch_alter_table('order_logistics_allocations', schema=None) as batch_op:
        batch_op.drop_column('pricing_breakdown_json')

    # 1. Remove per_km_rate column
    with op.batch_alter_table('logistics_partner_service_areas', schema=None) as batch_op:
        batch_op.drop_constraint('ck_lp_service_areas_per_km_nonnegative', type_='check')
        batch_op.drop_column('per_km_rate')

