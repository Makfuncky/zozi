"""Add GIN indexes to country_configs JSONB columns

Revision ID: m5n6o7p8q9r0
Revises: m0n1o2p3q4r5
Create Date: 2026-06-24 21:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'm5n6o7p8q9r0'
down_revision = 'm0n1o2p3q4r5'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(
        'idx_country_configs_payment_gateways_gin',
        'country_configs',
        [sa.text("payment_gateways_json gin_trgm_ops")],
        postgresql_using='gin'
    )
    op.create_index(
        'idx_country_configs_payout_methods_gin',
        'country_configs',
        [sa.text("payout_methods_json gin_trgm_ops")],
        postgresql_using='gin'
    )
    op.create_index(
        'idx_country_configs_commission_ranges_gin',
        'country_configs',
        [sa.text("suggested_commission_ranges_json gin_trgm_ops")],
        postgresql_using='gin'
    )
    op.create_index(
        'idx_country_configs_gateway_rankings_gin',
        'country_configs',
        [sa.text("suggested_gateway_rankings_json gin_trgm_ops")],
        postgresql_using='gin'
    )
    op.create_index(
        'idx_country_configs_restricted_categories_gin',
        'country_configs',
        [sa.text("restricted_categories_json gin_trgm_ops")],
        postgresql_using='gin'
    )
    op.create_index(
        'idx_country_configs_cities_gin',
        'country_configs',
        [sa.text("cities_json gin_trgm_ops")],
        postgresql_using='gin'
    )
    op.create_index(
        'idx_country_configs_public_holidays_gin',
        'country_configs',
        [sa.text("public_holidays_json gin_trgm_ops")],
        postgresql_using='gin'
    )
    op.create_index(
        'idx_country_configs_working_days_gin',
        'country_configs',
        [sa.text("working_days_json gin_trgm_ops")],
        postgresql_using='gin'
    )
    op.create_index(
        'idx_country_configs_supplier_requirements_gin',
        'country_configs',
        [sa.text("supplier_requirements_json gin_trgm_ops")],
        postgresql_using='gin'
    )
    op.create_index(
        'idx_country_configs_logistics_zones_gin',
        'country_configs',
        [sa.text("logistics_zones_json gin_trgm_ops")],
        postgresql_using='gin'
    )
    op.create_index(
        'idx_country_configs_consumer_behavior_gin',
        'country_configs',
        [sa.text("consumer_behavior_profile_json gin_trgm_ops")],
        postgresql_using='gin'
    )
    op.create_index(
        'idx_country_configs_default_language_gin',
        'country_configs',
        [sa.text("supported_languages_json gin_trgm_ops")],
        postgresql_using='gin'
    )
    op.create_index(
        'idx_country_configs_features_gin',
        'country_configs',
        [sa.text("feature_flags_json gin_trgm_ops")],
        postgresql_using='gin'
    )


def downgrade():
    op.drop_index('idx_country_configs_features_gin', table_name='country_configs')
    op.drop_index('idx_country_configs_default_language_gin', table_name='country_configs')
    op.drop_index('idx_country_configs_consumer_behavior_gin', table_name='country_configs')
    op.drop_index('idx_country_configs_logistics_zones_gin', table_name='country_configs')
    op.drop_index('idx_country_configs_supplier_requirements_gin', table_name='country_configs')
    op.drop_index('idx_country_configs_working_days_gin', table_name='country_configs')
    op.drop_index('idx_country_configs_public_holidays_gin', table_name='country_configs')
    op.drop_index('idx_country_configs_cities_gin', table_name='country_configs')
    op.drop_index('idx_country_configs_restricted_categories_gin', table_name='country_configs')
    op.drop_index('idx_country_configs_gateway_rankings_gin', table_name='country_configs')
    op.drop_index('idx_country_configs_commission_ranges_gin', table_name='country_configs')
    op.drop_index('idx_country_configs_payout_methods_gin', table_name='country_configs')
    op.drop_index('idx_country_configs_payment_gateways_gin', table_name='country_configs')

