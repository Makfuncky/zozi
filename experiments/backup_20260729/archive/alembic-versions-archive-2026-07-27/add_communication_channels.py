"""add employee communication and internal channels

Revision ID: add_communication_channels
Revises: c2d3e4f5a6b7
Create Date: 2026-06-29 19:20:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'add_communication_channels'
down_revision = 's_add_communic'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create employee_communication_threads table
    op.create_table('employee_communication_threads',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('country_code', sa.String(10), nullable=True),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=False),
        sa.Column('participants', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('last_message_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['country_code'], ['country_configs.code'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_emp_comm_country'), 'employee_communication_threads', ['country_code'], unique=False)
    op.create_index(op.f('ix_emp_comm_entity'), 'employee_communication_threads', ['entity_type', 'entity_id'], unique=False)

    # Create external_contact_masking table
    op.create_table('external_contact_masking',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('external_contact_type', sa.String(50), nullable=False),
        sa.Column('external_contact_id', sa.Integer(), nullable=False),
        sa.Column('masked_phone', sa.String(20), nullable=True),
        sa.Column('masked_email', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_masking_user'), 'external_contact_masking', ['user_id'], unique=False)

    # Create internal_channels table
    op.create_table('internal_channels',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('country_code', sa.String(10), nullable=True),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['country_code'], ['country_configs.code'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_internal_channel_country'), 'internal_channels', ['country_code'], unique=False)
    op.create_index(op.f('ix_internal_channel_entity'), 'internal_channels', ['entity_type', 'entity_id'], unique=False)

    # Create internal_channel_members table
    op.create_table('internal_channel_members',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('channel_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(20), nullable=True),
        sa.Column('joined_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['channel_id'], ['internal_channels.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_unique_constraint('uq_channel_member', 'internal_channel_members', ['channel_id', 'user_id'])

    # Create internal_messages table
    op.create_table('internal_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('channel_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('message_type', sa.String(20), nullable=True),
        sa.Column('is_masked', sa.Boolean(), nullable=True),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['channel_id'], ['internal_channels.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_internal_msg_channel'), 'internal_messages', ['channel_id'], unique=False)
    op.create_index(op.f('ix_internal_msg_user'), 'internal_messages', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_table('internal_messages')
    op.drop_table('internal_channel_members')
    op.drop_table('internal_channels')
    op.drop_table('external_contact_masking')
    op.drop_table('employee_communication_threads')
