"""create_event_tables

Revision ID: 20260730_0004
Revises: 20260730_0003
Create Date: 2026-07-30
"""
import os
import sys
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(_project_root, "alembic"))
sys.path.insert(0, _project_root)

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from migration_helpers import safe_create_index, safe_create_table, safe_drop_index, safe_drop_table


revision: str = "20260730_0004"
down_revision: Union[str, None] = "20260730_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        op.execute(
            "CREATE TABLE IF NOT EXISTS outbox_events ("
            "id INTEGER NOT NULL PRIMARY KEY, "
            "uuid VARCHAR(36) NOT NULL UNIQUE, "
            "event_type VARCHAR(100) NOT NULL, "
            "aggregate_type VARCHAR(50) NOT NULL, "
            "aggregate_id INTEGER NOT NULL, "
            "payload_json TEXT NOT NULL, "
            "status VARCHAR(20) NOT NULL DEFAULT 'pending', "
            "country_code VARCHAR(3), "
            "published_at DATETIME, "
            "created_at DATETIME NOT NULL, "
            "updated_at DATETIME NOT NULL, "
            "is_deleted BOOLEAN NOT NULL DEFAULT 0, "
            "deleted_at DATETIME, "
            "deleted_by_id INTEGER, "
            "created_by_id INTEGER, "
            "updated_by_id INTEGER, "
            "CONSTRAINT fk_outbox_deleted_by FOREIGN KEY(deleted_by_id) REFERENCES users (id), "
            "CONSTRAINT fk_outbox_created_by FOREIGN KEY(created_by_id) REFERENCES users (id), "
            "CONSTRAINT fk_outbox_updated_by FOREIGN KEY(updated_by_id) REFERENCES users (id)"
            ")"
        )
        op.execute("CREATE INDEX IF NOT EXISTS ix_outbox_aggregate ON outbox_events (aggregate_type, aggregate_id)")
        op.execute("CREATE INDEX IF NOT EXISTS ix_outbox_status ON outbox_events (status, created_at)")
        op.execute("CREATE INDEX IF NOT EXISTS ix_outbox_country ON outbox_events (country_code)")

        op.execute(
            "CREATE TABLE IF NOT EXISTS inbox_events ("
            "id INTEGER NOT NULL PRIMARY KEY, "
            "idempotency_key VARCHAR(64) NOT NULL UNIQUE, "
            "event_type VARCHAR(100) NOT NULL, "
            "status VARCHAR(20) NOT NULL DEFAULT 'pending', "
            "processed_at DATETIME, "
            "country_code VARCHAR(3), "
            "created_at DATETIME NOT NULL, "
            "updated_at DATETIME NOT NULL, "
            "is_deleted BOOLEAN NOT NULL DEFAULT 0, "
            "deleted_at DATETIME, "
            "deleted_by_id INTEGER, "
            "created_by_id INTEGER, "
            "updated_by_id INTEGER, "
            "CONSTRAINT fk_inbox_deleted_by FOREIGN KEY(deleted_by_id) REFERENCES users (id), "
            "CONSTRAINT fk_inbox_created_by FOREIGN KEY(created_by_id) REFERENCES users (id), "
            "CONSTRAINT fk_inbox_updated_by FOREIGN KEY(updated_by_id) REFERENCES users (id)"
            ")"
        )
        op.execute("CREATE INDEX IF NOT EXISTS ix_inbox_event_type ON inbox_events (event_type)")
        op.execute("CREATE INDEX IF NOT EXISTS ix_inbox_processed ON inbox_events (processed_at)")
        op.execute("CREATE INDEX IF NOT EXISTS ix_inbox_country ON inbox_events (country_code)")

        op.execute(
            "CREATE TABLE IF NOT EXISTS event_retry_queue ("
            "id INTEGER NOT NULL PRIMARY KEY, "
            "event_id INTEGER NOT NULL, "
            "attempt INTEGER NOT NULL DEFAULT 1, "
            "next_attempt_at DATETIME NOT NULL, "
            "last_error TEXT, "
            "country_code VARCHAR(3), "
            "created_at DATETIME NOT NULL, "
            "updated_at DATETIME NOT NULL, "
            "is_deleted BOOLEAN NOT NULL DEFAULT 0, "
            "deleted_at DATETIME, "
            "deleted_by_id INTEGER, "
            "created_by_id INTEGER, "
            "updated_by_id INTEGER, "
            "CONSTRAINT fk_retry_event_id FOREIGN KEY(event_id) REFERENCES outbox_events (id), "
            "CONSTRAINT fk_retry_deleted_by FOREIGN KEY(deleted_by_id) REFERENCES users (id), "
            "CONSTRAINT fk_retry_created_by FOREIGN KEY(created_by_id) REFERENCES users (id), "
            "CONSTRAINT fk_retry_updated_by FOREIGN KEY(updated_by_id) REFERENCES users (id)"
            ")"
        )
        op.execute("CREATE INDEX IF NOT EXISTS ix_retry_event ON event_retry_queue (event_id)")
        op.execute("CREATE INDEX IF NOT EXISTS ix_retry_next_attempt ON event_retry_queue (next_attempt_at)")
        op.execute("CREATE INDEX IF NOT EXISTS ix_retry_country ON event_retry_queue (country_code)")

        op.execute(
            "CREATE TABLE IF NOT EXISTS event_dead_letter ("
            "id INTEGER NOT NULL PRIMARY KEY, "
            "event_id INTEGER NOT NULL, "
            "payload_json TEXT NOT NULL, "
            "failed_at DATETIME NOT NULL, "
            "reason VARCHAR(255), "
            "resolved_by INTEGER, "
            "country_code VARCHAR(3), "
            "created_at DATETIME NOT NULL, "
            "updated_at DATETIME NOT NULL, "
            "is_deleted BOOLEAN NOT NULL DEFAULT 0, "
            "deleted_at DATETIME, "
            "deleted_by_id INTEGER, "
            "created_by_id INTEGER, "
            "updated_by_id INTEGER, "
            "CONSTRAINT fk_dlq_event_id FOREIGN KEY(event_id) REFERENCES outbox_events (id), "
            "CONSTRAINT fk_dlq_resolved_by FOREIGN KEY(resolved_by) REFERENCES users (id), "
            "CONSTRAINT fk_dlq_deleted_by FOREIGN KEY(deleted_by_id) REFERENCES users (id), "
            "CONSTRAINT fk_dlq_created_by FOREIGN KEY(created_by_id) REFERENCES users (id), "
            "CONSTRAINT fk_dlq_updated_by FOREIGN KEY(updated_by_id) REFERENCES users (id)"
            ")"
        )
        op.execute("CREATE INDEX IF NOT EXISTS ix_dlq_event ON event_dead_letter (event_id)")
        op.execute("CREATE INDEX IF NOT EXISTS ix_dlq_failed ON event_dead_letter (failed_at)")
        op.execute("CREATE INDEX IF NOT EXISTS ix_dlq_country ON event_dead_letter (country_code)")
    else:
        op.execute("CREATE SCHEMA IF NOT EXISTS analytics")

        safe_create_table(op, 
            "outbox_events",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False),
            sa.Column("event_type", sa.String(length=100), nullable=False),
            sa.Column("aggregate_type", sa.String(length=50), nullable=False),
            sa.Column("aggregate_id", sa.Integer(), nullable=False),
            sa.Column("payload_json", sa.Text(), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False),
            sa.Column("country_code", sa.String(length=3), nullable=True),
            sa.Column("published_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.Column("is_deleted", sa.Boolean(), nullable=False),
            sa.Column("deleted_at", sa.DateTime(), nullable=True),
            sa.Column("deleted_by_id", sa.Integer(), nullable=True),
            sa.Column("created_by_id", sa.Integer(), nullable=True),
            sa.Column("updated_by_id", sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], name="fk_outbox_created_by"),
            sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"], name="fk_outbox_updated_by"),
            sa.ForeignKeyConstraint(["deleted_by_id"], ["users.id"], name="fk_outbox_deleted_by"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid", name="uq_outbox_uuid"),
            schema="analytics",
        )
        safe_create_index(op, "ix_outbox_aggregate", "outbox_events", ["aggregate_type", "aggregate_id"], schema="analytics")
        safe_create_index(op, "ix_outbox_status", "outbox_events", ["status", "created_at"], schema="analytics")
        safe_create_index(op, "ix_outbox_country", "outbox_events", ["country_code"], schema="analytics")

        safe_create_table(op, 
            "inbox_events",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("idempotency_key", sa.String(length=64), nullable=False),
            sa.Column("event_type", sa.String(length=100), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False),
            sa.Column("processed_at", sa.DateTime(), nullable=True),
            sa.Column("country_code", sa.String(length=3), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.Column("is_deleted", sa.Boolean(), nullable=False),
            sa.Column("deleted_at", sa.DateTime(), nullable=True),
            sa.Column("deleted_by_id", sa.Integer(), nullable=True),
            sa.Column("created_by_id", sa.Integer(), nullable=True),
            sa.Column("updated_by_id", sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], name="fk_inbox_created_by"),
            sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"], name="fk_inbox_updated_by"),
            sa.ForeignKeyConstraint(["deleted_by_id"], ["users.id"], name="fk_inbox_deleted_by"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("idempotency_key", name="uq_inbox_idempotency_key"),
            schema="analytics",
        )
        safe_create_index(op, "ix_inbox_event_type", "inbox_events", ["event_type"], schema="analytics")
        safe_create_index(op, "ix_inbox_processed", "inbox_events", ["processed_at"], schema="analytics")
        safe_create_index(op, "ix_inbox_country", "inbox_events", ["country_code"], schema="analytics")

        safe_create_table(op, 
            "event_retry_queue",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("event_id", sa.Integer(), nullable=False),
            sa.Column("attempt", sa.Integer(), nullable=False),
            sa.Column("next_attempt_at", sa.DateTime(), nullable=False),
            sa.Column("last_error", sa.Text(), nullable=True),
            sa.Column("country_code", sa.String(length=3), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.Column("is_deleted", sa.Boolean(), nullable=False),
            sa.Column("deleted_at", sa.DateTime(), nullable=True),
            sa.Column("deleted_by_id", sa.Integer(), nullable=True),
            sa.Column("created_by_id", sa.Integer(), nullable=True),
            sa.Column("updated_by_id", sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], name="fk_retry_created_by"),
            sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"], name="fk_retry_updated_by"),
            sa.ForeignKeyConstraint(["deleted_by_id"], ["users.id"], name="fk_retry_deleted_by"),
            sa.ForeignKeyConstraint(["event_id"], ["analytics.outbox_events.id"], name="fk_retry_event_id"),
            sa.PrimaryKeyConstraint("id"),
            schema="analytics",
        )
        safe_create_index(op, "ix_retry_event", "event_retry_queue", ["event_id"], schema="analytics")
        safe_create_index(op, "ix_retry_next_attempt", "event_retry_queue", ["next_attempt_at"], schema="analytics")
        safe_create_index(op, "ix_retry_country", "event_retry_queue", ["country_code"], schema="analytics")

        safe_create_table(op, 
            "event_dead_letter",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("event_id", sa.Integer(), nullable=False),
            sa.Column("payload_json", sa.Text(), nullable=False),
            sa.Column("failed_at", sa.DateTime(), nullable=False),
            sa.Column("reason", sa.String(length=255), nullable=True),
            sa.Column("resolved_by", sa.Integer(), nullable=True),
            sa.Column("country_code", sa.String(length=3), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.Column("is_deleted", sa.Boolean(), nullable=False),
            sa.Column("deleted_at", sa.DateTime(), nullable=True),
            sa.Column("deleted_by_id", sa.Integer(), nullable=True),
            sa.Column("created_by_id", sa.Integer(), nullable=True),
            sa.Column("updated_by_id", sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], name="fk_dlq_created_by"),
            sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"], name="fk_dlq_updated_by"),
            sa.ForeignKeyConstraint(["deleted_by_id"], ["users.id"], name="fk_dlq_deleted_by"),
            sa.ForeignKeyConstraint(["event_id"], ["analytics.outbox_events.id"], name="fk_dlq_event_id"),
            sa.ForeignKeyConstraint(["resolved_by"], ["users.id"], name="fk_dlq_resolved_by"),
            sa.PrimaryKeyConstraint("id"),
            schema="analytics",
        )
        safe_create_index(op, "ix_dlq_event", "event_dead_letter", ["event_id"], schema="analytics")
        safe_create_index(op, "ix_dlq_failed", "event_dead_letter", ["failed_at"], schema="analytics")
        safe_create_index(op, "ix_dlq_country", "event_dead_letter", ["country_code"], schema="analytics")


def downgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        op.execute("DROP INDEX IF EXISTS ix_dlq_country")
        op.execute("DROP INDEX IF EXISTS ix_dlq_failed")
        op.execute("DROP INDEX IF EXISTS ix_dlq_event")
        op.execute("DROP TABLE IF EXISTS event_dead_letter")
        op.execute("DROP INDEX IF EXISTS ix_retry_country")
        op.execute("DROP INDEX IF EXISTS ix_retry_next_attempt")
        op.execute("DROP INDEX IF EXISTS ix_retry_event")
        op.execute("DROP TABLE IF EXISTS event_retry_queue")
        op.execute("DROP INDEX IF EXISTS ix_inbox_country")
        op.execute("DROP INDEX IF EXISTS ix_inbox_processed")
        op.execute("DROP INDEX IF EXISTS ix_inbox_event_type")
        op.execute("DROP TABLE IF EXISTS inbox_events")
        op.execute("DROP INDEX IF EXISTS ix_outbox_country")
        op.execute("DROP INDEX IF EXISTS ix_outbox_status")
        op.execute("DROP INDEX IF EXISTS ix_outbox_aggregate")
        op.execute("DROP TABLE IF EXISTS outbox_events")
    else:
        safe_drop_index(op, "ix_dlq_country", table_name="event_dead_letter", schema="analytics")
        safe_drop_index(op, "ix_dlq_failed", table_name="event_dead_letter", schema="analytics")
        safe_drop_index(op, "ix_dlq_event", table_name="event_dead_letter", schema="analytics")
        safe_drop_table(op, "event_dead_letter", schema="analytics")
        safe_drop_index(op, "ix_retry_country", table_name="event_retry_queue", schema="analytics")
        safe_drop_index(op, "ix_retry_next_attempt", table_name="event_retry_queue", schema="analytics")
        safe_drop_index(op, "ix_retry_event", table_name="event_retry_queue", schema="analytics")
        safe_drop_table(op, "event_retry_queue", schema="analytics")
        safe_drop_index(op, "ix_inbox_country", table_name="inbox_events", schema="analytics")
        safe_drop_index(op, "ix_inbox_processed", table_name="inbox_events", schema="analytics")
        safe_drop_index(op, "ix_inbox_event_type", table_name="inbox_events", schema="analytics")
        safe_drop_table(op, "inbox_events", schema="analytics")
        safe_drop_index(op, "ix_outbox_country", table_name="outbox_events", schema="analytics")
        safe_drop_index(op, "ix_outbox_status", table_name="outbox_events", schema="analytics")
        safe_drop_index(op, "ix_outbox_aggregate", table_name="outbox_events", schema="analytics")
        safe_drop_table(op, "outbox_events", schema="analytics")
