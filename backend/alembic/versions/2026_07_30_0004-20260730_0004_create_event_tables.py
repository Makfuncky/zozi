"""create_event_tables

Revision ID: 20260730_0004
Revises: 20260730_0003
Create Date: 2026-07-30

Creates four analytics-schema tables for the cross-domain event bus:
  * ``analytics.outbox_events``    — outbound event staging (per Law 3)
  * ``analytics.inbox_events``     — idempotent inbound consumer log
  * ``analytics.event_retry_queue`` — backoff-scheduled retry entries
  * ``analytics.event_dead_letter`` — permanent-failure DLQ (WIR-023 / OBS-003)

Dual-dialect support
--------------------
Both the SQLite (dev/test) and PostgreSQL (staging/prod) branches create the
same four tables with the same columns, FKs, and indexes.  The column
definitions are specified exactly once per table in the helper functions below
so that the two branches can never silently drift relative to each other.  Both
branches now use Alembic's ``op.create_table`` / ``op.create_index`` DDL;
SQLite does not support schemas, so its tables are created in the default
namespace.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# ---------------------------------------------------------------------------
# Shared column definitions (single source of truth per table)
# ---------------------------------------------------------------------------
# These lists of ``sa.Column`` objects are reused by both the SQLite
# and PostgreSQL branches via ``op.create_table``, ensuring that the two
# dialect paths stay in lock-step (WIR-024 / dual-maintenance fix).

def _outbox_columns() -> list[sa.Column]:
    return [
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("uuid", sa.String(length=36), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("aggregate_type", sa.String(length=50), nullable=False),
        sa.Column("aggregate_id", sa.Integer(), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("country_code", sa.String(length=3), nullable=True),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_by_id", sa.Integer(), nullable=True),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("updated_by_id", sa.Integer(), nullable=True),
    ]


def _outbox_fks() -> list[sa.ForeignKeyConstraint]:
    return [
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], name="fk_outbox_created_by"),
        sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"], name="fk_outbox_updated_by"),
        sa.ForeignKeyConstraint(["deleted_by_id"], ["users.id"], name="fk_outbox_deleted_by"),
    ]


def _outbox_pk() -> sa.PrimaryKeyConstraint:
    return sa.PrimaryKeyConstraint("id")


def _outbox_uq() -> sa.UniqueConstraint:
    return sa.UniqueConstraint("uuid", name="uq_outbox_uuid")


def _inbox_columns() -> list[sa.Column]:
    return [
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=64), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("processed_at", sa.DateTime(), nullable=True),
        sa.Column("country_code", sa.String(length=3), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_by_id", sa.Integer(), nullable=True),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("updated_by_id", sa.Integer(), nullable=True),
    ]


def _inbox_fks() -> list[sa.ForeignKeyConstraint]:
    return [
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], name="fk_inbox_created_by"),
        sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"], name="fk_inbox_updated_by"),
        sa.ForeignKeyConstraint(["deleted_by_id"], ["users.id"], name="fk_inbox_deleted_by"),
    ]


def _inbox_pk() -> sa.PrimaryKeyConstraint:
    return sa.PrimaryKeyConstraint("id")


def _inbox_uq() -> sa.UniqueConstraint:
    return sa.UniqueConstraint("idempotency_key", name="uq_inbox_idempotency_key")


def _retry_columns() -> list[sa.Column]:
    return [
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("attempt", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("next_attempt_at", sa.DateTime(), nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("country_code", sa.String(length=3), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_by_id", sa.Integer(), nullable=True),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("updated_by_id", sa.Integer(), nullable=True),
    ]


def _retry_fks() -> list[sa.ForeignKeyConstraint]:
    return [
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], name="fk_retry_created_by"),
        sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"], name="fk_retry_updated_by"),
        sa.ForeignKeyConstraint(["deleted_by_id"], ["users.id"], name="fk_retry_deleted_by"),
        sa.ForeignKeyConstraint(["event_id"], ["analytics.outbox_events.id"], name="fk_retry_event_id"),
    ]


def _retry_pk() -> sa.PrimaryKeyConstraint:
    return sa.PrimaryKeyConstraint("id")


def _dlq_columns() -> list[sa.Column]:
    return [
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("failed_at", sa.DateTime(), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column("resolved_by", sa.Integer(), nullable=True),
        sa.Column("country_code", sa.String(length=3), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_by_id", sa.Integer(), nullable=True),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("updated_by_id", sa.Integer(), nullable=True),
    ]


def _dlq_fks() -> list[sa.ForeignKeyConstraint]:
    return [
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], name="fk_dlq_created_by"),
        sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"], name="fk_dlq_updated_by"),
        sa.ForeignKeyConstraint(["deleted_by_id"], ["users.id"], name="fk_dlq_deleted_by"),
        sa.ForeignKeyConstraint(["event_id"], ["analytics.outbox_events.id"], name="fk_dlq_event_id"),
        sa.ForeignKeyConstraint(["resolved_by"], ["users.id"], name="fk_dlq_resolved_by"),
    ]


def _dlq_pk() -> sa.PrimaryKeyConstraint:
    return sa.PrimaryKeyConstraint("id")


# ---------------------------------------------------------------------------
# Standard index names (shared across both dialect branches)
# ---------------------------------------------------------------------------
_OUTBOX_INDEXES = [
    ("ix_outbox_aggregate", ["aggregate_type", "aggregate_id"]),
    ("ix_outbox_status", ["status", "created_at"]),
    ("ix_outbox_country", ["country_code"]),
]
_INBOX_INDEXES = [
    ("ix_inbox_event_type", ["event_type"]),
    ("ix_inbox_processed", ["processed_at"]),
    ("ix_inbox_country", ["country_code"]),
]
_RETRY_INDEXES = [
    ("ix_retry_event", ["event_id"]),
    ("ix_retry_next_attempt", ["next_attempt_at"]),
    ("ix_retry_country", ["country_code"]),
]
_DLQ_INDEXES = [
    ("ix_dlq_event", ["event_id"]),
    ("ix_dlq_failed", ["failed_at"]),
    ("ix_dlq_country", ["country_code"]),
]


revision: str = "20260730_0004"
down_revision: Union[str, None] = "20260730_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        _upgrade_sqlite()
    else:
        _upgrade_postgres()


def _upgrade_sqlite() -> None:
    """Create event tables on SQLite using Alembic DDL (dev/test databases).

    The column and constraint set mirrors the PostgreSQL branch exactly; both
    paths are derived from the shared ``_*_columns()`` helpers above so drift
    is impossible.  SQLite does not support schemas, so tables are created
    in the default namespace.
    """
    op.create_table(
        "outbox_events",
        *_outbox_columns(),
        *_outbox_fks(),
        _outbox_pk(),
        _outbox_uq(),
        if_not_exists=True,
    )
    for idx_name, cols in _OUTBOX_INDEXES:
        op.create_index(idx_name, "outbox_events", list(cols), if_not_exists=True)

    op.create_table(
        "inbox_events",
        *_inbox_columns(),
        *_inbox_fks(),
        _inbox_pk(),
        _inbox_uq(),
        if_not_exists=True,
    )
    for idx_name, cols in _INBOX_INDEXES:
        op.create_index(idx_name, "inbox_events", list(cols), if_not_exists=True)

    op.create_table(
        "event_retry_queue",
        *_retry_columns(),
        *_retry_fks(),
        _retry_pk(),
        if_not_exists=True,
    )
    for idx_name, cols in _RETRY_INDEXES:
        op.create_index(idx_name, "event_retry_queue", list(cols), if_not_exists=True)

    op.create_table(
        "event_dead_letter",
        *_dlq_columns(),
        *_dlq_fks(),
        _dlq_pk(),
        if_not_exists=True,
    )
    for idx_name, cols in _DLQ_INDEXES:
        op.create_index(idx_name, "event_dead_letter", list(cols), if_not_exists=True)


def _upgrade_postgres() -> None:
    """Create event tables on PostgreSQL using SQLAlchemy DDL with schema qualifier."""
    op.execute("CREATE SCHEMA IF NOT EXISTS analytics")

    op.create_table(
        "outbox_events",
        *_outbox_columns(),
        *_outbox_fks(),
        _outbox_pk(),
        _outbox_uq(),
        schema="analytics",
    )
    for idx_name, cols in _OUTBOX_INDEXES:
        op.create_index(idx_name, "outbox_events", list(cols), schema="analytics")

    op.create_table(
        "inbox_events",
        *_inbox_columns(),
        *_inbox_fks(),
        _inbox_pk(),
        _inbox_uq(),
        schema="analytics",
    )
    for idx_name, cols in _INBOX_INDEXES:
        op.create_index(idx_name, "inbox_events", list(cols), schema="analytics")

    op.create_table(
        "event_retry_queue",
        *_retry_columns(),
        *_retry_fks(),
        _retry_pk(),
        schema="analytics",
    )
    for idx_name, cols in _RETRY_INDEXES:
        op.create_index(idx_name, "event_retry_queue", list(cols), schema="analytics")

    op.create_table(
        "event_dead_letter",
        *_dlq_columns(),
        *_dlq_fks(),
        _dlq_pk(),
        schema="analytics",
    )
    for idx_name, cols in _DLQ_INDEXES:
        op.create_index(idx_name, "event_dead_letter", list(cols), schema="analytics")


def downgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        op.drop_index("ix_dlq_country", table_name="event_dead_letter", if_exists=True)
        op.drop_index("ix_dlq_failed", table_name="event_dead_letter", if_exists=True)
        op.drop_index("ix_dlq_event", table_name="event_dead_letter", if_exists=True)
        op.drop_table("event_dead_letter", if_exists=True)
        op.drop_index("ix_retry_country", table_name="event_retry_queue", if_exists=True)
        op.drop_index("ix_retry_next_attempt", table_name="event_retry_queue", if_exists=True)
        op.drop_index("ix_retry_event", table_name="event_retry_queue", if_exists=True)
        op.drop_table("event_retry_queue", if_exists=True)
        op.drop_index("ix_inbox_country", table_name="inbox_events", if_exists=True)
        op.drop_index("ix_inbox_processed", table_name="inbox_events", if_exists=True)
        op.drop_index("ix_inbox_event_type", table_name="inbox_events", if_exists=True)
        op.drop_table("inbox_events", if_exists=True)
        op.drop_index("ix_outbox_country", table_name="outbox_events", if_exists=True)
        op.drop_index("ix_outbox_status", table_name="outbox_events", if_exists=True)
        op.drop_index("ix_outbox_aggregate", table_name="outbox_events", if_exists=True)
        op.drop_table("outbox_events", if_exists=True)
    else:
        op.drop_index("ix_dlq_country", table_name="event_dead_letter", schema="analytics")
        op.drop_index("ix_dlq_failed", table_name="event_dead_letter", schema="analytics")
        op.drop_index("ix_dlq_event", table_name="event_dead_letter", schema="analytics")
        op.drop_table("event_dead_letter", schema="analytics")
        op.drop_index("ix_retry_country", table_name="event_retry_queue", schema="analytics")
        op.drop_index("ix_retry_next_attempt", table_name="event_retry_queue", schema="analytics")
        op.drop_index("ix_retry_event", table_name="event_retry_queue", schema="analytics")
        op.drop_table("event_retry_queue", schema="analytics")
        op.drop_index("ix_inbox_country", table_name="inbox_events", schema="analytics")
        op.drop_index("ix_inbox_processed", table_name="inbox_events", schema="analytics")
        op.drop_index("ix_inbox_event_type", table_name="inbox_events", schema="analytics")
        op.drop_table("inbox_events", schema="analytics")
        op.drop_index("ix_outbox_country", table_name="outbox_events", schema="analytics")
        op.drop_index("ix_outbox_status", table_name="outbox_events", schema="analytics")
        op.drop_index("ix_outbox_aggregate", table_name="outbox_events", schema="analytics")
        op.drop_table("outbox_events", schema="analytics")
