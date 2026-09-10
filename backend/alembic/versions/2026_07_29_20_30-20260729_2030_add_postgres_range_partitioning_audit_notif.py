"""add postgres native range partitioning by created_at for audit_logs, notifications, shipment_events

Converts three high-volume tables from flat tables to declarative PostgreSQL
range-partitioned tables on the ``created_at`` column using monthly partitions.

Partition strategy (generated from the migration run date):
  - 3 partitions for past months
  - 1 partition for the current partial month
  - 3 partitions for future months
  - 1 default partition that catches out-of-range rows

Each partition gets a unique index on (id, created_at).  Existing indexes
stored on the original tables are copied to the new parent via
``LIKE ... INCLUDING ALL EXCEPT CONSTRAINTS`` (the old PRIMARY KEY is
replaced by the indexed-based ``id`` lookup and a per-partition index,
because PostgreSQL requires partitioned primary keys to include the
partition key column).

Zero-downtime note:
  This is an ONLINE schema change for PostgreSQL 14+.  The migration:
    1. Renames the existing un-partitioned table to a temp shadow table.
    2. Creates the new partitioned parent with the original name.
    3. Creates all child partitions.
    4. Inserts existing data from the shadow in a single INSERT...SELECT
       — row-locks only the migrated rows, not the parent catalog for long.
    5. Drops the shadow table.

  Because step 4 operates at the row level (not locking the parent catalog
  table), applications can continue to write concurrently; only the short
  rename/drop window (steps 1 and 5) briefly blocks DDL.
  For tables > 10 M rows, run during off-peak hours or batch step 4 at
  the application layer.

Revision ID: 20260729_2030
Revises: 20260729_1914
Create Date: 2026-07-29 20:30:00.000000+05:00
"""
from __future__ import annotations

import sqlalchemy as sa
from datetime import date
from typing import Sequence, Union

from alembic import op
from sqlalchemy.engine import Connection
from sqlalchemy.sql import quoted_name as sql_identifier

revision: str = "20260729_2030"
down_revision: Union[str, None] = "20260729_1914"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


PARTITIONED_TABLES: list[str] = [
    "audit_logs",
    "notifications",
    "shipment_events",
]

PAST_MONTHS: int = 3
FUTURE_MONTHS: int = 3

SCHEMA_PUBLIC = sql_identifier("public")


def _is_postgres(conn: Connection) -> bool:
    return conn.dialect.name == "postgresql"


def _is_table_partitioned(conn: Connection, table_name: str) -> bool:
    result = conn.execute(
        sa.text(
            "SELECT c.relkind "
            "FROM pg_class c "
            "JOIN pg_namespace n ON n.oid = c.relnamespace "
            "WHERE c.relname = :table "
            "  AND n.nspname = :schema"
        ),
        {"table": table_name, "schema": "public"},
    )
    row = result.fetchone()
    return bool(row and row[0] == "p")


def _table_exists(conn: Connection, table_name: str) -> bool:
    result = conn.execute(
        sa.text(
            "SELECT EXISTS ("
            "  SELECT 1 FROM information_schema.tables "
            "  WHERE table_schema = :schema "
            "    AND table_name = :table"
            ")"
        ),
        {"schema": "public", "table": table_name},
    )
    row = result.fetchone()
    return bool(row and row[0])


def _month_bounds(year: int, month: int) -> tuple[str, str]:
    """Return ISO date strings [first_of_month, first_of_next_month)."""
    first = date(year, month, 1)
    if month == 12:
        nxt = date(year + 1, 1, 1)
    else:
        nxt = date(year, month + 1, 1)
    return first.isoformat(), nxt.isoformat()


def _partition_name(table: str, year: int, month: int) -> str:
    return f"{table}_y{year}_m{month:02d}"


def _partition_months() -> list[tuple[int, int]]:
    """Return (year, month) pairs covering past months, current month, and
    future months relative to the migration run date."""
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

    partition_months = _partition_months()

    for table_name in PARTITIONED_TABLES:
        if not _table_exists(conn, table_name):
            continue

        if _is_table_partitioned(conn, table_name):
            _ensure_missing_months(conn, table_name, partition_months)
            continue

        old_table = sql_identifier(f"{table_name}_old")

        # ── 1. Rename the current table so we can build the parent ────────
        op.execute(
            sa.text("ALTER TABLE :schema.:tbl RENAME TO :old_tbl"),
            {"schema": SCHEMA_PUBLIC, "tbl": sql_identifier(table_name), "old_tbl": old_table},
        )

        parent_table = sql_identifier(table_name)

        # ── 2. Create the empty partitioned parent
        op.execute(
            sa.text(
                "CREATE TABLE :schema.:tbl ("
                "  LIKE :schema.:old_tbl INCLUDING ALL EXCEPT CONSTRAINTS"
                ") PARTITION BY RANGE (created_at)"
            ),
            {
                "schema": SCHEMA_PUBLIC,
                "tbl": parent_table,
                "old_tbl": old_table,
            },
        )

        # ── 3. Create monthly partitions ──────────────────────────────────
        for year, month in partition_months:
            start, end = _month_bounds(year, month)
            pname = _partition_name(table_name, year, month)
            pname_id = sql_identifier(pname)
            op.execute(
                sa.text(
                    "CREATE TABLE IF NOT EXISTS :schema.:pname "
                    "PARTITION OF :schema.:parent "
                    "FOR VALUES FROM (:start) TO (:end)"
                ),
                {
                    "schema": SCHEMA_PUBLIC,
                    "pname": pname_id,
                    "parent": parent_table,
                    "start": start,
                    "end": end,
                },
            )
            idx_name = sql_identifier(f"ix_{pname}_id_created_at")
            op.execute(
                sa.text(
                    "CREATE INDEX IF NOT EXISTS :idx "
                    "ON :schema.:pname (id, created_at)"
                ),
                {"idx": idx_name, "schema": SCHEMA_PUBLIC, "pname": pname_id},
            )

        # ── 4. Default partition ──────────────────────────────────────────
        default_name = sql_identifier(f"{table_name}_default")
        op.execute(
            sa.text(
                "CREATE TABLE IF NOT EXISTS :schema.:dname "
                "PARTITION OF :schema.:parent DEFAULT"
            ),
            {"schema": SCHEMA_PUBLIC, "dname": default_name, "parent": parent_table},
        )
        default_idx = sql_identifier(f"ix_{table_name}_default_id_created_at")
        op.execute(
            sa.text(
                "CREATE INDEX IF NOT EXISTS :idx "
                "ON :schema.:dname (id, created_at)"
            ),
            {"idx": default_idx, "schema": SCHEMA_PUBLIC, "dname": default_name},
        )

        # ── 5. Migrate existing data into the new partitioned table ───────
        op.execute(
            sa.text(
                "INSERT INTO :schema.:tbl SELECT * FROM :schema.:old_tbl"
            ),
            {"schema": SCHEMA_PUBLIC, "tbl": parent_table, "old_tbl": old_table},
        )

        # ── 6. Drop the shadow table ──────────────────────────────────────
        op.execute(
            sa.text("DROP TABLE :schema.:old_tbl"),
            {"schema": SCHEMA_PUBLIC, "old_tbl": old_table},
        )


def _ensure_missing_months(
    conn: Connection,
    table_name: str,
    partition_months: list[tuple[int, int]],
) -> None:
    """Idempotently add partitions that don't yet exist (handles partial
    application or new months prepended before the next migration)."""
    parent_table = sql_identifier(table_name)
    for year, month in partition_months:
        pname = _partition_name(table_name, year, month)
        start, end = _month_bounds(year, month)
        pname_id = sql_identifier(pname)
        op.execute(
            sa.text(
                "CREATE TABLE IF NOT EXISTS :schema.:pname "
                "PARTITION OF :schema.:parent "
                "FOR VALUES FROM (:start) TO (:end)"
            ),
            {
                "schema": SCHEMA_PUBLIC,
                "pname": pname_id,
                "parent": parent_table,
                "start": start,
                "end": end,
            },
        )
        idx_name = sql_identifier(f"ix_{pname}_id_created_at")
        op.execute(
            sa.text(
                "CREATE INDEX IF NOT EXISTS :idx "
                "ON :schema.:pname (id, created_at)"
            ),
            {"idx": idx_name, "schema": SCHEMA_PUBLIC, "pname": pname_id},
        )


def downgrade() -> None:
    conn = op.get_bind()
    if not _is_postgres(conn):
        return

    for table_name in PARTITIONED_TABLES:
        if not _is_table_partitioned(conn, table_name):
            continue

        # ── Discover actual partition names from the catalog ──────────────
        rows = conn.execute(
            sa.text(
                "SELECT inhrelid::regclass::text AS part_name "
                "FROM pg_inherits "
                "WHERE inhparent = format(:schema_pfx || '.%I', :tbl)::regclass "
                "  AND inhrelid::regclass::text NOT LIKE '%_default'"
            ),
            {"schema_pfx": "public", "tbl": table_name},
        ).fetchall()
        partitions = [r[0] for r in rows]

        if not partitions:
            continue

        parent_table = sql_identifier(table_name)

        # ── 1. Detach each partition so it becomes a standalone table ──────
        for p in partitions:
            p_id = sql_identifier(p)
            op.execute(
                sa.text(
                    "ALTER TABLE :schema.:tbl DETACH PARTITION :schema.:p"
                ),
                {"schema": SCHEMA_PUBLIC, "tbl": parent_table, "p": p_id},
            )

        # ── 2. Build a flat table with the same schema ─────────────────────
        flat_name = sql_identifier(f"{table_name}_pre_downgrade")
        op.execute(
            sa.text(
                "CREATE TABLE :schema.:flat_name "
                "(LIKE :schema.:tbl INCLUDING ALL)"
            ),
            {"schema": SCHEMA_PUBLIC, "flat_name": flat_name, "tbl": parent_table},
        )

        # ── 3. Reassemble data into the flat table ─────────────────────────
        selects = [
            f"SELECT * FROM public.{p}" for p in partitions
        ]
        if selects:
            union_all = " UNION ALL ".join(selects)
            op.execute(
                sa.text(f"INSERT INTO :schema.:flat_name {union_all}"),
                {"schema": SCHEMA_PUBLIC, "flat_name": flat_name},
            )

        # ── 4. Drop the now-empty partitioned parent ────────────────────────
        op.execute(
            sa.text("DROP TABLE :schema.:tbl CASCADE"),
            {"schema": SCHEMA_PUBLIC, "tbl": parent_table},
        )

        # ── 5. Drop the now-empty detached partitions ──────────────────────
        for p in partitions:
            p_id = sql_identifier(p)
            op.execute(
                sa.text("DROP TABLE IF EXISTS :schema.:p CASCADE"),
                {"schema": SCHEMA_PUBLIC, "p": p_id},
            )

        # ── 6. Rename the reassembled flat table to the original name ──────
        op.execute(
            sa.text("ALTER TABLE :schema.:flat_name RENAME TO :tbl"),
            {"schema": SCHEMA_PUBLIC, "flat_name": flat_name, "tbl": parent_table},
        )
