"""Add notification fields and country cities relationship.

Revision ID: c2d3e4f5a6b7
Revises: a1b2c3d4e5f7b_add_country_management_tables
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'c2d3e4f5a6b7'
down_revision = 'a1b2c3d4e5f7b'  # Now exists
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('notifications', sa.Column('channel', sa.String(), server_default='in_app', nullable=True))
    op.add_column('notifications', sa.Column('priority', sa.String(), server_default='medium', nullable=True))
    op.add_column('notifications', sa.Column('read_at', sa.DateTime(), nullable=True))
    op.add_column('notifications', sa.Column('template', sa.String(), nullable=True))
    op.add_column('notifications', sa.Column('variables', sa.JSON(), nullable=True))
    op.add_column('notifications', sa.Column('scheduled_at', sa.DateTime(), nullable=True))
    op.add_column('notifications', sa.Column('status', sa.String(), server_default='delivered', nullable=True))
    
    op.create_index(op.f('ix_notifications_is_read'), 'notifications', ['is_read'], unique=False)
    op.create_index(op.f('ix_notifications_user_read'), 'notifications', ['user_id', 'is_read'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_notifications_user_read'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_is_read'), table_name='notifications')
    op.drop_column('notifications', 'status')
    op.drop_column('notifications', 'scheduled_at')
    op.drop_column('notifications', 'variables')
    op.drop_column('notifications', 'template')
    op.drop_column('notifications', 'read_at')
    op.drop_column('notifications', 'priority')
    op.drop_column('notifications', 'channel')
