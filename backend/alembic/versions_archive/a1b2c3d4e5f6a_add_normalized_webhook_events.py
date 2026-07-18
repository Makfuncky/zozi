"""Add normalized webhook events table

Revision ID: a1b2c3d4e5f6a
Revises: s_a1b2c3d4e5f6
Create Date: 2026-07-09 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'a1b2c3d4e5f6a'
down_revision = 's_a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'normalized_webhook_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('provider_code', sa.String(length=60), nullable=False),
        sa.Column('gateway_event_id', sa.String(), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('environment', sa.String(length=20), default='live'),
        sa.Column('processed_at', sa.DateTime(), default=sa.func.utcnow()),
        sa.Column('zozi_order_id', sa.String(), nullable=True),
        sa.Column('gateway_transaction_id', sa.String(), nullable=True),
        sa.Column('gateway_customer_id', sa.String(), nullable=True),
        sa.Column('gross_amount', sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=False),
        sa.Column('gateway_fee', sa.Numeric(precision=14, scale=4), default=sa.text('0')),
        sa.Column('net_settlement', sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column('fraud_score', sa.Integer(), nullable=True),
        sa.Column('three_ds_status', sa.String(length=30), nullable=True),
        sa.Column('avs_result', sa.String(length=30), nullable=True),
        sa.Column('raw_payload', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('provider_code', 'gateway_event_id', name='uq_normalized_webhook_event'),
    )
    
    op.create_index('ix_normalized_webhook_order', 'normalized_webhook_events', ['zozi_order_id'])
    op.create_index('ix_normalized_webhook_status', 'normalized_webhook_events', ['status'])
    op.create_index('ix_normalized_webhook_processed_at', 'normalized_webhook_events', ['processed_at'])
    op.create_index('ix_normalized_webhook_provider_event', 'normalized_webhook_events', ['provider_code', 'gateway_event_id'])


def downgrade() -> None:
    op.drop_index('ix_normalized_webhook_provider_event', table_name='normalized_webhook_events')
    op.drop_index('ix_normalized_webhook_processed_at', table_name='normalized_webhook_events')
    op.drop_index('ix_normalized_webhook_status', table_name='normalized_webhook_events')
    op.drop_index('ix_normalized_webhook_order', table_name='normalized_webhook_events')
    op.drop_table('normalized_webhook_events')
