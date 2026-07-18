"""Add GIN indexes for JSONB columns in country_configs

Revision ID: m1n2o3p4q5r6
Revises: c1d2e3f4a5b6
Create Date: 2026-06-25 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'm1n2o3p4q5r6'
down_revision = "s_m1n2o3p4q5r6"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index('ix_country_configs_gin_commissions', 'country_configs', ['suggested_commission_ranges_json'], postgresql_using='gin')
    op.create_index('ix_country_configs_gin_gateways', 'country_configs', ['suggested_gateway_rankings_json'], postgresql_using='gin')
    op.create_index('ix_country_configs_gin_behavior', 'country_configs', ['consumer_behavior_profile_json'], postgresql_using='gin')
    op.create_index('ix_country_configs_gin_public_holidays', 'country_configs', ['public_holidays_json'], postgresql_using='gin')
    op.create_index('ix_country_configs_gin_working_days', 'country_configs', ['working_days_json'], postgresql_using='gin')
    op.create_index('ix_country_configs_gin_restricted_cats', 'country_configs', ['restricted_categories_json'], postgresql_using='gin')
    op.create_index('ix_country_configs_gin_payment_gws', 'country_configs', ['payment_gateways_json'], postgresql_using='gin')
    op.create_index('ix_country_configs_gin_logistics_zones', 'country_configs', ['logistics_zones_json'], postgresql_using='gin')


def downgrade():
    op.drop_index('ix_country_configs_gin_logistics_zones', table_name='country_configs')
    op.drop_index('ix_country_configs_gin_payment_gws', table_name='country_configs')
    op.drop_index('ix_country_configs_gin_restricted_cats', table_name='country_configs')
    op.drop_index('ix_country_configs_gin_working_days', table_name='country_configs')
    op.drop_index('ix_country_configs_gin_public_holidays', table_name='country_configs')
    op.drop_index('ix_country_configs_gin_behavior', table_name='country_configs')
    op.drop_index('ix_country_configs_gin_gateways', table_name='country_configs')
    op.drop_index('ix_country_configs_gin_commissions', table_name='country_configs')

