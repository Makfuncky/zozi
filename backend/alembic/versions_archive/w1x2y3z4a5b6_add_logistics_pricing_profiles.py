"""add_logistics_pricing_profiles

Revision ID: w1x2y3z4a5b6
Revises: v1w2x3y4z5a6
Create Date: 2026-04-08 13:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'w1x2y3z4a5b6'
down_revision: Union[str, Sequence[str], None] = 'v1w2x3y4z5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'logistics_pricing_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('partner_id', sa.Integer(), sa.ForeignKey('logistics_partners.id'), nullable=False),
        sa.Column('service_area_id', sa.Integer(), sa.ForeignKey('logistics_partner_service_areas.id'), nullable=True),
        sa.Column('profile_name', sa.String(length=120), nullable=True),
        sa.Column('base_in_city_fee', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('base_inter_city_fee', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('per_km_rate', sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column('per_kg_rate', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('minimum_charge', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('fuel_multiplier', sa.Numeric(precision=8, scale=4), nullable=True),
        sa.Column('bulk_discount_threshold_kg', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('bulk_discount_percent', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('currency', sa.String(length=10), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('approval_status', sa.String(length=30), nullable=False),
        sa.Column('review_note', sa.Text(), nullable=True),
        sa.Column('reviewed_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('base_in_city_fee IS NULL OR base_in_city_fee >= 0', name='ck_lp_pricing_profiles_base_in_city_nonnegative'),
        sa.CheckConstraint('base_inter_city_fee IS NULL OR base_inter_city_fee >= 0', name='ck_lp_pricing_profiles_base_inter_city_nonnegative'),
        sa.CheckConstraint('per_km_rate IS NULL OR per_km_rate >= 0', name='ck_lp_pricing_profiles_per_km_nonnegative'),
        sa.CheckConstraint('per_kg_rate IS NULL OR per_kg_rate >= 0', name='ck_lp_pricing_profiles_per_kg_nonnegative'),
        sa.CheckConstraint('minimum_charge IS NULL OR minimum_charge >= 0', name='ck_lp_pricing_profiles_minimum_charge_nonnegative'),
        sa.CheckConstraint('fuel_multiplier IS NULL OR fuel_multiplier > 0', name='ck_lp_pricing_profiles_fuel_multiplier_positive'),
        sa.CheckConstraint('bulk_discount_threshold_kg IS NULL OR bulk_discount_threshold_kg >= 0', name='ck_lp_pricing_profiles_bulk_threshold_nonnegative'),
        sa.CheckConstraint('bulk_discount_percent IS NULL OR (bulk_discount_percent >= 0 AND bulk_discount_percent <= 100)', name='ck_lp_pricing_profiles_bulk_percent_range'),
    )
    op.create_index('ix_logistics_pricing_profiles_id', 'logistics_pricing_profiles', ['id'], unique=False)
    op.create_index('ix_lp_pricing_profiles_partner_status', 'logistics_pricing_profiles', ['partner_id', 'approval_status'], unique=False)
    op.create_index('ix_lp_pricing_profiles_service_area', 'logistics_pricing_profiles', ['service_area_id', 'approval_status'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_lp_pricing_profiles_service_area', table_name='logistics_pricing_profiles')
    op.drop_index('ix_lp_pricing_profiles_partner_status', table_name='logistics_pricing_profiles')
    op.drop_index('ix_logistics_pricing_profiles_id', table_name='logistics_pricing_profiles')
    op.drop_table('logistics_pricing_profiles')

