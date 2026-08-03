"""partition_journal_entries - add partitioning for journal_entries table

Revision ID: 20260731_0012
Revises: 20260731_0011
Create Date: 2026-07-31

Per DATABASE_SCOPE.md §7.2, journal_entries must be partitioned by created_at (monthly).
This migration extends the existing partitioning infrastructure to include journal_entries.
"""
from __future__ import annotations

from datetime import date
from typing import Sequence, Union

from alembic import op
from sqlalchemy.engine import Connection

revision: str = "20260731_0012"
down_revision: Union[str, None] = "20260731_0011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

PAST_MONTHS: int = 3
FUTURE_MONTHS: int = 3


def _is_postgres(conn: Connection) -> bool:
    return conn.dialect.name == "postgresql"


def _is_table_partitioned(conn: Connection, table_name: str) -> bool:
    result = conn.execute(
        """
        SELECT c.relkind
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE c.relname = :table
          AND n.nspname = 'finance'
        """,
        {"table": table_name},
    )
    row = result.fetchone()
    return bool(row and row[0] == "p")


def _table_exists(conn: Connection, table_name: str) -> bool:
    result = conn.execute(
        """
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'finance'
              AND table_name = :table
        )
        """,
        {"table": table_name},
    )
    row = result.fetchone()
    return bool(row and row[0])


def _month_bounds(year: int, month: int) -> tuple[str, str]:
    """Return ISO date strings [first_of_month, first_of_next_month)."""
    first = date(year, month, 1)
    if month == 12:
        nxt = date(year + 1, 1, 1)
    else:
        nxt = date(year + month + 1, 1)
    return first.isoformat(), nxt.isoformat()


def _partition_name(table: str, year: int, month: int) -> str:
    return f"{table}_y{year}_m{month:02d}"


def _partition_months() -> list[tuple[int, int]]:
    """Return (year, month) pairs covering past months, current month, and future months."""
    today = date.today()
    raw: list[tuple[int, int]] = []
    for offset in range(-PAST_MONTHS, FUTURE_MONTHS + 1):
        m = today.month + offset
        y = today.year
        while m <= 0:
            m += 12
            y -= 1
        while m > 12:
            m -= 12
            y += 1
        raw.append((y, m))
    seen: set[tuple[int, int]] = set()
    result: list[tuple[int, int]] = []
    for item in raw:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def upgrade() -> None:
    conn = op.get_bind()
    if not _is_postgres(conn):
        return

    table_name = "journal_entries"
    if not _table_exists(conn, table_name):
        return

    if _is_table_partitioned(conn, table_name):
        partition_months = _partition_months()
        for year, month in partition_months:
            pname = _partition_name(table_name, year, month)
            start, end = _month_bounds(year, month)
            op.execute(
                f"""
                CREATE TABLE IF NOT EXISTS finance.{pname}
                PARTITION OF finance.{table_name}
                FOR VALUES FROM ('{start}') TO ('{end}')
                """
            )
        return

    op.execute(
        f"ALTER TABLE finance.{table_name} RENAME TO {table_name}_old"
    )

    op.execute(
        f"""
        CREATE TABLE finance.{table_name} (
            LIKE finance.{table_name}_old INCLUDING ALL EXCEPT CONSTRAINTS
        ) PARTITION BY RANGE (created_at)
        """
    )

    partition_months = _partition_months()
    for year, month in partition_months:
        start, end = _month_bounds(year, month)
        pname = _partition_name(table_name, year, month)
        op.execute(
            f"""
            CREATE TABLE IF NOT EXISTS finance.{pname}
            PARTITION OF finance.{table_name}
            FOR VALUES FROM ('{start}') TO ('{end}')
            """
        )
        op.execute(
            f"""
            CREATE INDEX IF NOT EXISTS ix_{pname}_id_created_at
            ON finance.{pname} (id, created_at)
            """
        )

    op.execute(
        f"""
        CREATE TABLE IF NOT EXISTS finance.{table_name}_default
        PARTITION OF finance.{table_name} DEFAULT
        """
    )

    op.execute(
        f"""
        CREATE INDEX IF NOT EXISTS ix_{table_name}_default_id_created_at
        ON finance.{table_name}_default (id, created_at)
        """
    )

    insert_sql = "INSERT INTO finance." + table_name + " SELECT * FROM finance." + table_name + "_old"
    op.execute(insert_sql)

    drop_sql = "DROP TABLE finance." + table_name + "_old"
    op.execute(drop_sql)


def downgrade() -> None:
    conn = op.get_bind()
    if not _is_postgres(conn):
        return

    table_name = "journal_entries"
    if not _is_table_partitioned(conn, table_name):
        return

    rows = conn.execute(
        """
        SELECT inhrelid::regclass::text AS part_name
        FROM pg_inherits
        WHERE inhparent = format('finance.%I', :tbl)::regclass
          AND inhrelid::regclass::text NOT LIKE '%_default'
        """,
        {"tbl": table_name},
    ).fetchall()
    partitions = [r[0] for r in rows]

    if not partitions:
        return

    for p in reversed(partitions):
        op.execute(
            f"ALTER TABLE finance.{table_name} DETACH PARTITION finance.{p}"
        )

    flat_name = f"{table_name}_pre_downgrade"
    op.execute(
        f"CREATE TABLE finance.{flat_name} "
        f"(LIKE finance.{table_name} INCLUDING ALL)"
    )

    selects = ["SELECT * FROM finance." + p for p in partitions]
    if selects:
        union_all = " UNION ALL ".join(selects)
        insert_sql = "INSERT INTO finance." + flat_name + " " + union_all
        op.execute(insert_sql)

    drop_sql = "DROP TABLE finance." + table_name + " CASCADE"
    op.execute(drop_sql)

    for p in partitions:
        drop_part_sql = "DROP TABLE IF EXISTS finance." + p + " CASCADE"
        op.execute(drop_part_sql)

    rename_sql = "ALTER TABLE finance." + flat_name + " RENAME TO " + table_name
    op.execute(rename_sql)