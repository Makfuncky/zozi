"""add_email_delivery_events_and_suppressions

Revision ID: z7b8c9d0e1f2
Revises: y4z5a6b7c8d9
Create Date: 2026-04-04 02:10:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = "z7b8c9d0e1f2"
down_revision: Union[str, Sequence[str], None] = "y4z5a6b7c8d9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing = inspector.get_table_names()

    if "email_suppressions" not in existing:
        op.create_table(
            "email_suppressions",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("email", sa.String(length=255), nullable=False),
            sa.Column("reason", sa.String(length=100), nullable=False),
            sa.Column("source", sa.String(length=100), nullable=False, server_default="system"),
            sa.Column("provider", sa.String(length=50), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("first_event_id", sa.String(length=255), nullable=True),
            sa.Column("last_event_id", sa.String(length=255), nullable=True),
            sa.Column("suppressed_at", sa.DateTime(), nullable=True),
            sa.Column("last_event_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.CheckConstraint("status IN ('active', 'inactive')", name="ck_email_suppressions_status_valid"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("email", name="uq_email_suppressions_email"),
        )
        op.create_index("ix_email_suppressions_email", "email_suppressions", ["email"], unique=True)

    if "email_delivery_events" not in existing:
        op.create_table(
            "email_delivery_events",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("event_id", sa.String(length=255), nullable=True),
            sa.Column("processor", sa.String(length=50), nullable=False),
            sa.Column("message_id", sa.String(length=255), nullable=True),
            sa.Column("recipient_email", sa.String(length=255), nullable=False),
            sa.Column("subject", sa.String(length=500), nullable=True),
            sa.Column("purpose", sa.String(length=50), nullable=True),
            sa.Column("event_type", sa.String(length=50), nullable=False),
            sa.Column("source", sa.String(length=50), nullable=False, server_default="application"),
            sa.Column("campaign_recipient_id", sa.Integer(), nullable=True),
            sa.Column("payload", sa.Text(), nullable=True),
            sa.Column("occurred_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["campaign_recipient_id"], ["campaign_recipients.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_email_delivery_events_event_id", "email_delivery_events", ["event_id"], unique=False)
        op.create_index("ix_email_delivery_events_message_id", "email_delivery_events", ["message_id"], unique=False)
        op.create_index("ix_email_delivery_events_recipient_email", "email_delivery_events", ["recipient_email"], unique=False)
        op.create_index("ix_email_delivery_events_recipient_created", "email_delivery_events", ["recipient_email", "created_at"], unique=False)
        op.create_index("ix_email_delivery_events_processor_event", "email_delivery_events", ["processor", "event_id"], unique=False)
        op.create_index("ix_email_delivery_events_event_type_created", "email_delivery_events", ["event_type", "created_at"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing = inspector.get_table_names()

    if "email_delivery_events" in existing:
        op.drop_table("email_delivery_events")
    if "email_suppressions" in existing:
        op.drop_table("email_suppressions")

