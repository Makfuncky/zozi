"""add_email_marketing_models

Revision ID: 78b323427448
Revises: 7b91a42af432
Create Date: 2026-03-17 07:12:36.568007

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '78b323427448'
down_revision: Union[str, Sequence[str], None] = '7b91a42af432'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Newsletter subscribers table
    op.create_table('newsletter_subscribers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=True),
        sa.Column('last_name', sa.String(length=100), nullable=True),
        sa.Column('source', sa.String(length=50), nullable=True, default='website'),
        sa.Column('preferences', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('subscribed_at', sa.DateTime(), nullable=True),
        sa.Column('unsubscribed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index(op.f('ix_newsletter_subscribers_email'), 'newsletter_subscribers', ['email'], unique=False)
    op.create_index(op.f('ix_newsletter_subscribers_id'), 'newsletter_subscribers', ['id'], unique=False)

    # Email templates table
    op.create_table('email_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('subject', sa.String(length=500), nullable=False),
        sa.Column('html_content', sa.Text(), nullable=False),
        sa.Column('text_content', sa.Text(), nullable=True),
        sa.Column('template_type', sa.String(length=50), nullable=True, default='marketing'),
        sa.Column('variables', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_email_templates_id'), 'email_templates', ['id'], unique=False)
    op.create_index(op.f('ix_email_templates_name'), 'email_templates', ['name'], unique=True)

    # Email campaigns table
    op.create_table('email_campaigns',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('subject', sa.String(length=500), nullable=False),
        sa.Column('html_content', sa.Text(), nullable=False),
        sa.Column('text_content', sa.Text(), nullable=True),
        sa.Column('template_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=True, default='draft'),
        sa.Column('send_at', sa.DateTime(), nullable=True),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('target_audience', sa.String(length=50), nullable=True, default='all'),
        sa.Column('recipient_count', sa.Integer(), nullable=True, default=0),
        sa.Column('sent_count', sa.Integer(), nullable=True, default=0),
        sa.Column('opened_count', sa.Integer(), nullable=True, default=0),
        sa.Column('clicked_count', sa.Integer(), nullable=True, default=0),
        sa.Column('bounced_count', sa.Integer(), nullable=True, default=0),
        sa.Column('unsubscribed_count', sa.Integer(), nullable=True, default=0),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['template_id'], ['email_templates.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_email_campaigns_id'), 'email_campaigns', ['id'], unique=False)

    # Campaign recipients table
    op.create_table('campaign_recipients',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('campaign_id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True, default='pending'),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('opened_at', sa.DateTime(), nullable=True),
        sa.Column('clicked_at', sa.DateTime(), nullable=True),
        sa.Column('bounced_at', sa.DateTime(), nullable=True),
        sa.Column('unsubscribed_at', sa.DateTime(), nullable=True),
        sa.Column('tracking_id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['campaign_id'], ['email_campaigns.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tracking_id')
    )
    op.create_index(op.f('ix_campaign_recipients_campaign_email'), 'campaign_recipients', ['campaign_id', 'email'], unique=False)
    op.create_index(op.f('ix_campaign_recipients_email'), 'campaign_recipients', ['email'], unique=False)
    op.create_index(op.f('ix_campaign_recipients_id'), 'campaign_recipients', ['id'], unique=False)
    op.create_index(op.f('ix_campaign_recipients_tracking_id'), 'campaign_recipients', ['tracking_id'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('campaign_recipients')
    op.drop_table('email_campaigns')
    op.drop_table('email_templates')
    op.drop_table('newsletter_subscribers')

