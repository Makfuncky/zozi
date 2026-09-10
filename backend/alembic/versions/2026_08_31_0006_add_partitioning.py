"""Add range partitioning for hot append-only tables

Revision ID: 20260831_0006
Revises: 20260831_0005
Create Date: 2026-08-31
"""
import sqlalchemy as sa
from typing import Sequence, Union

from alembic import op
from sqlalchemy.sql import quoted_name as sql_identifier

revision: str = "20260831_0006"
down_revision: Union[str, None] = "20260831_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        return  # Partitioning not supported in SQLite

    # ── Range Partitioning (from document §7.2) ────────────────────────────
    # Monthly partitions for hot append-only tables

    # Audit logs - partitioned by month
    op.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS audit.audit_logs_partitioned (
            LIKE audit.audit_logs INCLUDING ALL
        ) PARTITION BY RANGE (created_at)
    """))

    for month in range(1, 13):
        start_date = f"2026-{month:02d}-01"
        if month == 12:
            end_date = "2027-01-01"
        else:
            end_date = f"2026-{month + 1:02d}-01"

        pname = sql_identifier(f"audit.audit_logs_y2026m{month:02d}")
        op.execute(
            sa.text(
                "CREATE TABLE IF NOT EXISTS :pname "
                "PARTITION OF audit.audit_logs_partitioned "
                "FOR VALUES FROM (:start) TO (:end)"
            ),
            {"pname": pname, "start": start_date, "end": end_date},
        )

    # Journal entries - partitioned by month
    op.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS finance.journal_entries_partitioned (
            LIKE finance.journal_entries INCLUDING ALL
        ) PARTITION BY RANGE (created_at)
    """))

    for month in range(1, 13):
        start_date = f"2026-{month:02d}-01"
        if month == 12:
            end_date = "2027-01-01"
        else:
            end_date = f"2026-{month + 1:02d}-01"

        pname = sql_identifier(f"finance.journal_entries_y2026m{month:02d}")
        op.execute(
            sa.text(
                "CREATE TABLE IF NOT EXISTS :pname "
                "PARTITION OF finance.journal_entries_partitioned "
                "FOR VALUES FROM (:start) TO (:end)"
            ),
            {"pname": pname, "start": start_date, "end": end_date},
        )

    # Shipment events - partitioned by month
    op.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS logistics.shipment_events_partitioned (
            LIKE logistics.shipment_events INCLUDING ALL
        ) PARTITION BY RANGE (created_at)
    """))

    for month in range(1, 13):
        start_date = f"2026-{month:02d}-01"
        if month == 12:
            end_date = "2027-01-01"
        else:
            end_date = f"2026-{month + 1:02d}-01"

        pname = sql_identifier(f"logistics.shipment_events_y2026m{month:02d}")
        op.execute(
            sa.text(
                "CREATE TABLE IF NOT EXISTS :pname "
                "PARTITION OF logistics.shipment_events_partitioned "
                "FOR VALUES FROM (:start) TO (:end)"
            ),
            {"pname": pname, "start": start_date, "end": end_date},
        )

    # Chat messages - partitioned by month
    op.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS comms.chat_messages_partitioned (
            LIKE comms.chat_messages INCLUDING ALL
        ) PARTITION BY RANGE (created_at)
    """))

    for month in range(1, 13):
        start_date = f"2026-{month:02d}-01"
        if month == 12:
            end_date = "2027-01-01"
        else:
            end_date = f"2026-{month + 1:02d}-01"

        pname = sql_identifier(f"comms.chat_messages_y2026m{month:02d}")
        op.execute(
            sa.text(
                "CREATE TABLE IF NOT EXISTS :pname "
                "PARTITION OF comms.chat_messages_partitioned "
                "FOR VALUES FROM (:start) TO (:end)"
            ),
            {"pname": pname, "start": start_date, "end": end_date},
        )


def downgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        return

    # Drop partitioned tables
    for _schema, table in [
        ("audit", "audit_logs_partitioned"),
        ("finance", "journal_entries_partitioned"),
        ("logistics", "shipment_events_partitioned"),
        ("comms", "chat_messages_partitioned"),
    ]:
        t = sql_identifier(table)
        op.execute(
            sa.text('DROP TABLE IF EXISTS :t CASCADE'),
            {"t": t},
        )
