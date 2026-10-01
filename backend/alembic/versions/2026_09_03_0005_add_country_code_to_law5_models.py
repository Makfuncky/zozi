"""Phase C (Law 5): add country_code String(2) to 54 business tables.

Closes audit findings #13 in MASTER_AUDIT.md. Models in domains/*/models/*.py
without a country_code column get one added (nullable, ISO 3166-1 alpha-2).
Per Law 20 the column type is String(2). Per Law 5 it is the orthogonal scope
axis. Indexes are added in a follow-up migration to keep this one idempotent
when the table was created via create_all() in dev (column will already exist).

Revision ID: 2026_09_03_0005
Revises: 2026_09_03_0004
Create Date: 2026-09-03
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "2026_09_03_0005"
down_revision: Union[str, None] = "2026_09_03_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_TABLES = [
        ("comms", "entity_chat_threads"),
        ("comms", "video_room_participants"),
        ("comms", "group_chat_members"),
        ("comms", "escalation_sla_logs"),
        ("comms", "entity_chat_messages"),
        ("comms", "video_room_recordings"),
        ("comms", "direct_chat_messages"),
        ("comms", "group_chat_messages"),
        ("comms", "announcements"),
        ("comms", "help_categories"),
        ("comms", "proxy_channels"),
        ("comms", "proxy_sessions"),
        ("comms", "proxy_messages"),
        ("comms", "proxy_call_logs"),
        ("comms", "external_contact_maskings"),
        ("comms", "communication_audit_trails"),
        ("comms", "internal_channel_members"),
        ("comms", "internal_messages"),
        ("comms", "chat_read_receipts"),
        ("comms", "chat_attachments"),
        ("comms", "email_folders"),
        ("comms", "news_sources"),
        ("comms", "internal_notices"),
        ("comms", "meeting_recordings"),
        ("comms", "incident_war_rooms"),
        ("comms", "incident_threads"),
        ("comms", "incident_action_items"),
        ("comms", "war_room_templates"),
        ("comms", "email_templates"),
        ("comms", "newsletter_subscribers"),
        ("comms", "email_campaign_logs"),
        ("comms", "campaign_recipients"),
        ("comms", "email_delivery_events"),
        ("comms", "email_suppressions"),
        ("comms", "email_runtime_configs"),
        ("country", "oman_delivery_zones"),
        ("customers", "cross_country_customer_sessions"),
        ("hr", "training_modules"),
        ("hr", "employee_trainings"),
        ("hr", "shift_handover_tasks"),
        ("hr", "employee_task_comments"),
        ("orders", "order_notifications"),
        ("security", "fraud_blacklists"),
        ("security", "manual_review_queues"),
        ("security", "device_fingerprints"),
        ("security", "credit_card_bins"),
        ("security", "return_abuse_patterns"),
        ("security", "ip_account_linkages"),
        ("security", "fraud_velocity_counters"),
        ("security", "fraud_case_assignments"),
        ("security", "dlp_violations"),
        ("security", "meeting_transcripts"),
        ("security", "meeting_action_items"),
        ("suppliers", "supplier_documents"),
    ]


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    for schema, table in _TABLES:
        if table not in inspector.get_table_names(schema=schema):
            continue
        existing = {c["name"] for c in inspector.get_columns(table, schema=schema)}
        if "country_code" in existing:
            continue
        op.add_column(
            table,
            sa.Column("country_code", sa.String(length=2), nullable=True),
            schema=schema,
        )
        # Index name derived from schema+table to avoid cross-schema conflicts
        idx_name = f"ix_{schema}_{table}_country_code"[:63]
        op.create_index(
            idx_name,
            table,
            ["country_code"],
            schema=schema,
            if_not_exists=True,
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    for schema, table in reversed(_TABLES):
        if table not in inspector.get_table_names(schema=schema):
            continue
        existing = {c["name"] for c in inspector.get_columns(table, schema=schema)}
        if "country_code" not in existing:
            continue
        idx_name = f"ix_{schema}_{table}_country_code"[:63]
        try:
            op.drop_index(idx_name, table_name=table, schema=schema)
        except Exception:
            pass
        op.drop_column(table, "country_code", schema=schema)
