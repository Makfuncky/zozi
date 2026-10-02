"""add_communication_model_audit_columns_file_012

Adds missing ``country_code`` column and composite indexes to ``comms`` tables
defined in ``backend/domains/comms/models/communication.py`` per
ARCHITECTURE_STACK.md Law 23 (every model MUST include created_at, updated_at,
country_code, is_deleted).

Findings resolved:
  FILE-012: communication.py models missing country_code, created_at/updated_at
            using Python-side defaults instead of server-side defaults.

Tables receiving ``country_code``:
  notifications, ticket_messages, faqs, proxy_channels, proxy_sessions,
  proxy_messages, proxy_call_logs, external_contact_maskings,
  communication_audit_trails, internal_channel_members, internal_messages,
  chat_read_receipts, chat_attachments, internal_emails, email_folders,
  masked_messages

Tables receiving composite ``country_code + created_at`` indexes:
  notifications, ticket_messages, faqs, proxy_channels, proxy_sessions,
  proxy_messages, proxy_call_logs, employee_communication_threads,
  external_contact_maskings, communication_audit_trails, internal_channels,
  internal_channel_members, internal_messages, chat_read_receipts,
  chat_attachments, internal_emails, email_folders, masked_messages

Idempotent and skipped on SQLite: dev/test databases are recreated from ORM
metadata which already carries the corrected column definitions.
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260930_0003"
down_revision: Union[str, None] = "20260930_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        return

    bind = op.get_bind()
    inspector = sa.inspect(bind)

    tables = [
        ("notifications", "ix_notifications_country_created"),
        ("ticket_messages", "ix_ticket_messages_country_created"),
        ("faqs", "ix_faqs_country_created"),
        ("proxy_channels", "ix_proxy_channels_country_created"),
        ("proxy_sessions", "ix_proxy_sessions_country_created"),
        ("proxy_messages", "ix_proxy_messages_country_created"),
        ("proxy_call_logs", "ix_proxy_call_logs_country_created"),
        ("employee_communication_threads", "ix_emp_comm_country_created"),
        ("external_contact_maskings", "ix_masking_country_created"),
        ("communication_audit_trails", "ix_comm_country_created"),
        ("internal_channels", "ix_internal_channels_country_created"),
        ("internal_channel_members", "ix_internal_channel_members_country_created"),
        ("internal_messages", "ix_internal_msg_country_created"),
        ("chat_read_receipts", "ix_chat_read_receipts_country_created"),
        ("chat_attachments", "ix_chat_attachments_country_created"),
        ("internal_emails", "ix_internal_emails_country_created"),
        ("email_folders", "ix_email_folders_country_created"),
        ("masked_messages", "ix_masked_messages_country_created"),
    ]

    for table_name, idx_name in tables:
        existing_cols = {c["name"] for c in inspector.get_columns(table_name, schema="comms")}

        if "country_code" not in existing_cols:
            with op.batch_alter_table(table_name, schema="comms") as batch_op:
                batch_op.add_column(
                    sa.Column("country_code", sa.String(length=2), nullable=False)
                )

        existing_idxs = {i["name"] for i in inspector.get_indexes(table_name, schema="comms")}
        if idx_name not in existing_idxs:
            with op.batch_alter_table(table_name, schema="comms") as batch_op:
                batch_op.create_index(
                    idx_name,
                    ["country_code", "created_at"],
                )


def downgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        return

    bind = op.get_bind()
    inspector = sa.inspect(bind)

    tables = [
        ("notifications", "ix_notifications_country_created"),
        ("ticket_messages", "ix_ticket_messages_country_created"),
        ("faqs", "ix_faqs_country_created"),
        ("proxy_channels", "ix_proxy_channels_country_created"),
        ("proxy_sessions", "ix_proxy_sessions_country_created"),
        ("proxy_messages", "ix_proxy_messages_country_created"),
        ("proxy_call_logs", "ix_proxy_call_logs_country_created"),
        ("employee_communication_threads", "ix_emp_comm_country_created"),
        ("external_contact_maskings", "ix_masking_country_created"),
        ("communication_audit_trails", "ix_comm_country_created"),
        ("internal_channels", "ix_internal_channels_country_created"),
        ("internal_channel_members", "ix_internal_channel_members_country_created"),
        ("internal_messages", "ix_internal_msg_country_created"),
        ("chat_read_receipts", "ix_chat_read_receipts_country_created"),
        ("chat_attachments", "ix_chat_attachments_country_created"),
        ("internal_emails", "ix_internal_emails_country_created"),
        ("email_folders", "ix_email_folders_country_created"),
        ("masked_messages", "ix_masked_messages_country_created"),
    ]

    for table_name, idx_name in tables:
        existing_idxs = {i["name"] for i in inspector.get_indexes(table_name, schema="comms")}
        if idx_name in existing_idxs:
            with op.batch_alter_table(table_name, schema="comms") as batch_op:
                batch_op.drop_index(idx_name)

        existing_cols = {c["name"] for c in inspector.get_columns(table_name, schema="comms")}
        if "country_code" in existing_cols:
            with op.batch_alter_table(table_name, schema="comms") as batch_op:
                batch_op.drop_column("country_code")
