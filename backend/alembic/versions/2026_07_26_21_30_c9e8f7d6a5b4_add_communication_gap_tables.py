"""add_communication_gap_tables

Revision ID: c9e8f7d6a5b4
Revises: b81bfc888610
Create Date: 2026-07-26 21:30:00.000000+00:00

This migration creates the internal communication gap tables:
- internal_channels: Internal chat channels for team communication
- internal_channel_members: Channel membership with roles
- internal_messages: Messages within internal channels
- chat_reactions: Emoji reactions to messages
- chat_legal_holds: Legal hold records for chat rooms
- external_contact_masking: Masked external contact info
- communication_audit_trail: Audit trail for all communication
- employee_communication_threads: Employee-specific communication threads
- notifications: In-app notifications
- announcements: Company-wide announcements
- faqs: FAQ entries
- help_categories: Support FAQ categories
- proxy_channels: Phone/SMS proxy channels
- proxy_sessions: Proxy call sessions
- proxy_messages: Proxy message history
- proxy_call_logs: Call recording logs
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c9e8f7d6a5b4'
down_revision: Union[str, None] = 'b81bfc888610'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'internal_channels',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('channel_id', sa.String(36), nullable=False, unique=True, index=True),
        sa.Column('country_code', sa.String(10), nullable=True),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('allowed_roles', sa.JSON(), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['country_code'], ['country_configs.code']),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.Index('ix_internal_channel_entity', 'entity_type', 'entity_id'),
    )

    op.create_table(
        'internal_channel_members',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('channel_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(20), nullable=False, server_default='member'),
        sa.Column('joined_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['channel_id'], ['internal_channels.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.UniqueConstraint('channel_id', 'user_id', name='uq_channel_member'),
    )

    op.create_table(
        'internal_messages',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('channel_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('message_type', sa.String(20), nullable=False, server_default='text'),
        sa.Column('is_masked', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('is_deleted', sa.Boolean(), nullable=True),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['channel_id'], ['internal_channels.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.Index('ix_internal_msg_channel', 'channel_id'),
        sa.Index('ix_internal_msg_user', 'user_id'),
    )

    op.create_table(
        'chat_reactions',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('message_id', sa.Integer(), nullable=False),
        sa.Column('message_type', sa.String(30), nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=False),
        sa.Column('emoji', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('message_id', 'message_type', 'employee_id', 'emoji', name='uq_chat_reaction'),
        sa.Index('ix_chat_reaction_msg', 'message_id', 'message_type'),
    )

    op.create_table(
        'chat_legal_holds',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('room_id', sa.Integer(), nullable=False),
        sa.Column('room_type', sa.String(30), nullable=False),
        sa.Column('placed_by', sa.Integer(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('placed_at', sa.DateTime(), nullable=True),
        sa.Column('released_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['placed_by'], ['users.id']),
        sa.UniqueConstraint('room_id', 'room_type', name='uq_legal_hold_room'),
    )

    op.create_table(
        'external_contact_masking',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('external_contact_type', sa.String(50), nullable=False),
        sa.Column('external_contact_id', sa.Integer(), nullable=False),
        sa.Column('masked_phone', sa.String(20), nullable=True),
        sa.Column('masked_email', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.UniqueConstraint('user_id', 'external_contact_type', 'external_contact_id', name='uq_masking_contact'),
        sa.Index('ix_masking_user', 'user_id'),
    )

    op.create_table(
        'communication_audit_trail',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('channel', sa.String(50), nullable=False),
        sa.Column('content_preview', sa.Text(), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.Index('ix_comm_entity', 'entity_type', 'entity_id'),
        sa.Index('ix_comm_user', 'user_id', 'created_at'),
    )

    op.create_table(
        'employee_communication_threads',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('country_code', sa.String(10), nullable=True),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=False),
        sa.Column('participants', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('last_message_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['country_code'], ['country_configs.code']),
        sa.Index('ix_emp_comm_entity', 'entity_type', 'entity_id'),
    )

    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('type', sa.String(), nullable=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('channel', sa.String(), nullable=False, server_default='in_app'),
        sa.Column('priority', sa.String(), nullable=False, server_default='medium'),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.Column('link', sa.String(), nullable=True),
        sa.Column('template', sa.String(), nullable=True),
        sa.Column('variables', sa.JSON(), nullable=True),
        sa.Column('scheduled_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='delivered'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('country_code', sa.String(10), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.Index('ix_notifications_user_id', 'user_id'),
        sa.Index('ix_notifications_is_read', 'is_read'),
        sa.Index('ix_notifications_user_read', 'user_id', 'is_read'),
    )

    op.create_table(
        'announcements',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('starts_at', sa.DateTime(), nullable=True),
        sa.Column('ends_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )

    op.create_table(
        'faqs',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('answer', sa.Text(), nullable=False),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('country_code', sa.String(10), nullable=True),
        sa.Index('ix_faqs_country_code', 'country_code'),
    )

    op.create_table(
        'help_categories',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )

    op.create_table(
        'proxy_channels',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('entity_type', sa.String(), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=False),
        sa.Column('proxy_phone', sa.String(), nullable=False, unique=True),
        sa.Column('proxy_email', sa.String(), nullable=False, unique=True),
        sa.Column('participants', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Index('idx_proxy_entity', 'entity_type', 'entity_id'),
    )

    op.create_table(
        'proxy_sessions',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('channel_id', sa.Integer(), nullable=False),
        sa.Column('participant_one_id', sa.Integer(), nullable=False),
        sa.Column('participant_two_id', sa.Integer(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('is_encrypted', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('session_metadata', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['channel_id'], ['proxy_channels.id']),
        sa.ForeignKeyConstraint(['participant_one_id'], ['users.id']),
        sa.ForeignKeyConstraint(['participant_two_id'], ['users.id']),
    )

    op.create_table(
        'proxy_messages',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('sender_id', sa.Integer(), nullable=False),
        sa.Column('recipient_id', sa.Integer(), nullable=False),
        sa.Column('message_type', sa.String(), nullable=False, server_default='text'),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('is_masked', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['proxy_sessions.id']),
        sa.ForeignKeyConstraint(['sender_id'], ['users.id']),
        sa.ForeignKeyConstraint(['recipient_id'], ['users.id']),
    )

    op.create_table(
        'proxy_call_logs',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('channel_id', sa.Integer(), nullable=False),
        sa.Column('caller_id', sa.Integer(), nullable=False),
        sa.Column('callee_id', sa.Integer(), nullable=False),
        sa.Column('direction', sa.String(), nullable=False),
        sa.Column('duration_seconds', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('call_recording_url', sa.String(), nullable=True),
        sa.Column('is_recorded', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['channel_id'], ['proxy_channels.id']),
        sa.ForeignKeyConstraint(['caller_id'], ['users.id']),
        sa.ForeignKeyConstraint(['callee_id'], ['users.id']),
    )


def downgrade() -> None:
    op.drop_table('proxy_call_logs')
    op.drop_table('proxy_messages')
    op.drop_table('proxy_sessions')
    op.drop_table('proxy_channels')
    op.drop_table('help_categories')
    op.drop_table('faqs')
    op.drop_table('announcements')
    op.drop_table('notifications')
    op.drop_table('employee_communication_threads')
    op.drop_table('communication_audit_trail')
    op.drop_table('external_contact_masking')
    op.drop_table('chat_legal_holds')
    op.drop_table('chat_reactions')
    op.drop_table('internal_messages')
    op.drop_table('internal_channel_members')
    op.drop_table('internal_channels')