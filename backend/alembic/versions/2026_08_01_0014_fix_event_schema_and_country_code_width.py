"""fix_event_schema_and_country_code_width

Move the transactional outbox/inbox/retry/DLQ event tables from the
``analytics`` schema (incorrectly assigned by migration 0005) to the
``configuration`` schema, matching the ORM models in ``events.py``
(Constitution §2.13, ADR-014, ADR-018).

Also adds ``version`` and ``delete_reason`` columns that the ORM
declares but migration 0004 omitted, and fixes ``payout_currency``
width on ``country_configs`` and ``country_economics`` to VARCHAR(3)
(finding *(c)* in App. F).

Revision ID: 20260801_0014
Revises: 20260801_0013
Create Date: 2026-08-01
"""
import os
import sys
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(_project_root, "alembic"))
sys.path.insert(0, _project_root)

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from migration_helpers import safe_add_column


revision: str = "20260801_0014"
down_revision: Union[str, None] = "20260801_0013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_EVENT_TABLES = ["outbox_events", "inbox_events", "event_retry_queue", "event_dead_letter"]


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        return

    op.execute('CREATE SCHEMA IF NOT EXISTS configuration')
    op.execute('CREATE SCHEMA IF NOT EXISTS analytics')

    for tbl in _EVENT_TABLES:
        op.execute(
            'ALTER TABLE IF EXISTS analytics."%s" SET SCHEMA "configuration"'
            % tbl
        )

    op.execute(
        'ALTER TABLE IF EXISTS configuration.event_retry_queue '
        'DROP CONSTRAINT IF EXISTS fk_retry_event_id'
    )
    op.execute(
        'ALTER TABLE IF EXISTS configuration.event_retry_queue '
        'ADD CONSTRAINT fk_retry_event_id '
        'FOREIGN KEY(event_id) REFERENCES configuration.outbox_events(id)'
    )

    op.execute(
        'ALTER TABLE IF EXISTS configuration.event_dead_letter '
        'DROP CONSTRAINT IF EXISTS fk_dlq_event_id'
    )
    op.execute(
        'ALTER TABLE IF EXISTS configuration.event_dead_letter '
        'ADD CONSTRAINT fk_dlq_event_id '
        'FOREIGN KEY(event_id) REFERENCES configuration.outbox_events(id)'
    )

    for tbl in _EVENT_TABLES:
        safe_add_column(op, tbl, sa.Column("version", sa.Integer, nullable=False, server_default="1"),
                        schema="configuration")
        safe_add_column(op, tbl, sa.Column("delete_reason", sa.Text, nullable=True),
                        schema="configuration")

    op.execute(
        "ALTER TABLE country.country_configs ALTER COLUMN payout_currency TYPE VARCHAR(3)"
    )
    op.execute(
        "ALTER TABLE country.country_economics ALTER COLUMN payout_currency TYPE VARCHAR(3)"
    )


def downgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        return

    op.execute(
        "ALTER TABLE country.country_configs ALTER COLUMN payout_currency TYPE VARCHAR(10)"
    )
    op.execute(
        "ALTER TABLE country.country_economics ALTER COLUMN payout_currency TYPE VARCHAR(10)"
    )

    for tbl in _EVENT_TABLES:
        with op.batch_alter_table(tbl, schema="configuration") as batch:
            batch.drop_column("delete_reason")
            batch.drop_column("version")

    op.execute(
        'ALTER TABLE configuration.event_retry_queue '
        'DROP CONSTRAINT IF EXISTS fk_retry_event_id'
    )
    op.execute(
        'ALTER TABLE configuration.event_retry_queue '
        'ADD CONSTRAINT fk_retry_event_id '
        'FOREIGN KEY(event_id) REFERENCES analytics.outbox_events(id)'
    )

    op.execute(
        'ALTER TABLE configuration.event_dead_letter '
        'DROP CONSTRAINT IF EXISTS fk_dlq_event_id'
    )
    op.execute(
        'ALTER TABLE configuration.event_dead_letter '
        'ADD CONSTRAINT fk_dlq_event_id '
        'FOREIGN KEY(event_id) REFERENCES analytics.outbox_events(id)'
    )

    for tbl in _EVENT_TABLES:
        op.execute(
            'ALTER TABLE IF EXISTS configuration."%s" SET SCHEMA "analytics"'
            % tbl
        )
