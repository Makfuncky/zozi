"""Add MediaAsset and fraud detection models.

Revision ID: m2n3o4p5q6r7
Revises: c1d2e3f4a5b6
Create Date: 2026-06-25 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'm2n3o4p5q6r7'
down_revision = "s_m2n3o4p5q6r7"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('media_assets',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('entity_type', sa.String(30), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=False),
        sa.Column('media_type', sa.String(20), nullable=False),
        sa.Column('file_name', sa.String(255), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('mime_type', sa.String(100), nullable=False),
        sa.Column('storage_path', sa.String(500), nullable=False),
        sa.Column('cdn_url', sa.String(500), nullable=True),
        sa.Column('alt_text', sa.String(255), nullable=True),
        sa.Column('caption', sa.String(255), nullable=True),
        sa.Column('is_primary', sa.Boolean(), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(20), nullable=True),
        sa.Column('uploaded_by', sa.Integer(), nullable=True),
        sa.Column('country_code', sa.String(10), nullable=True),
        sa.Column('metadata_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('storage_path')
    )
    op.create_index('ix_media_asset_entity', 'media_assets', ['entity_type', 'entity_id'])
    op.create_index('ix_media_asset_path', 'media_assets', ['storage_path'])
    op.create_index('ix_media_asset_type_status', 'media_assets', ['media_type', 'status'])
    op.create_index('ix_media_assets_country_code', 'media_assets', ['country_code'])

    op.create_table('fraud_events',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('order_id', sa.Integer(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_fraud_events_severity', 'fraud_events', ['severity'])

    op.create_table('fraud_blacklist',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('entity_type', sa.String(20), nullable=False),
        sa.Column('entity_value', sa.String(255), nullable=False),
        sa.Column('reason', sa.String(200), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_fraud_blacklist_entity', 'fraud_blacklist', ['entity_type', 'entity_value'])

    op.create_table('fraud_rules',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('rule_type', sa.String(50), nullable=False),
        sa.Column('condition', sa.Text(), nullable=False),
        sa.Column('threshold', sa.Float(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('manual_review_queue',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('entity_type', sa.String(30), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=False),
        sa.Column('reason', sa.String(200), nullable=False),
        sa.Column('assigned_to', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['assigned_to'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_manual_review_queue_status', 'manual_review_queue', ['status'])

    op.create_table('ip_reputations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('ip_address', sa.String(45), nullable=False),
        sa.Column('reputation_score', sa.Integer(), nullable=True),
        sa.Column('last_seen', sa.DateTime(), nullable=True),
        sa.Column('threat_types', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_ip_reputations_ip', 'ip_reputations', ['ip_address'], unique=True)

    op.create_table('device_fingerprints',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('fingerprint_hash', sa.String(64), nullable=False),
        sa.Column('first_seen', sa.DateTime(), nullable=True),
        sa.Column('last_seen', sa.DateTime(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('risk_score', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_device_fingerprints_hash', 'device_fingerprints', ['fingerprint_hash'], unique=True)

    op.create_table('ip_account_linkages',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('ip_address', sa.String(45), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('first_seen', sa.DateTime(), nullable=True),
        sa.Column('last_seen', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('supplier_fraud_indicators',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('supplier_id', sa.Integer(), nullable=False),
        sa.Column('indicator_type', sa.String(50), nullable=False),
        sa.Column('value', sa.Numeric(12, 2), nullable=True),
        sa.Column('risk_score', sa.Numeric(5, 2), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['supplier_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('logistics_fraud_indicators',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('partner_id', sa.Integer(), nullable=False),
        sa.Column('indicator_type', sa.String(50), nullable=False),
        sa.Column('value', sa.Numeric(12, 2), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('first_seen', sa.DateTime(), nullable=True),
        sa.Column('last_seen', sa.DateTime(), nullable=True),
        sa.Column('request_count', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['partner_id'], ['logistics_partners.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_logistics_fraud_indicators_ip', 'logistics_fraud_indicators', ['ip_address'])


def downgrade():
    op.drop_table('logistics_fraud_indicators')
    op.drop_table('supplier_fraud_indicators')
    op.drop_table('ip_account_linkages')
    op.drop_table('device_fingerprints')
    op.drop_table('ip_reputations')
    op.drop_table('manual_review_queue')
    op.drop_table('fraud_rules')
    op.drop_table('fraud_blacklist')
    op.drop_table('fraud_events')
    op.drop_table('media_assets')

