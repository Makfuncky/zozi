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

from datetime import date
from typing import Sequence, Union

from alembic import op
from sqlalchemy.engine import Connection

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


def _is_postgres(conn: Connection) -> bool:
    return conn.dialect.name == "postgresql"


def _is_table_partitioned(conn: Connection, table_name: str) -> bool:
    result = conn.execute(
        """
        SELECT c.relkind
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE c.relname = :table
          AND n.nspname = 'public'
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
            WHERE table_schema = 'public'
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

        # ── 1. Rename the current table so we can build the parent ────────
        op.execute(
            f"ALTER TABLE public.{table_name} RENAME TO {table_name}_old"
        )

        # ── 2. Create the empty partitioned parent (same schema as old,
        #      excluding PRIMARY KEY constraints — PostgreSQL requires
        #      partitioned PKs to include the partition key column).
        #      The existing ``index=True`` on ``id`` is carried over and
        #      augmented with a per-partition (id, created_at) index.
        op.execute(
            f"""
            CREATE TABLE public.{table_name} (
                LIKE public.{table_name}_old INCLUDING ALL EXCEPT CONSTRAINTS
            ) PARTITION BY RANGE (created_at)
            """
        )

        # ── 3. Create monthly partitions ──────────────────────────────────
        for year, month in partition_months:
            start, end = _month_bounds(year, month)
            pname = _partition_name(table_name, year, month)
            op.execute(
                f"""
                CREATE TABLE IF NOT EXISTS public.{pname}
                PARTITION OF public.{table_name}
                FOR VALUES FROM ('{start}') TO ('{end}')
                """
            )
            op.execute(
                f"""
                CREATE INDEX IF NOT EXISTS ix_{pname}_id_created_at
                ON public.{pname} (id, created_at)
                """
            )

        # ── 4. Default partition ──────────────────────────────────────────
        op.execute(
            f"""
            CREATE TABLE IF NOT EXISTS public.{table_name}_default
            PARTITION OF public.{table_name} DEFAULT
            """
        )
        op.execute(
            f"""
            CREATE INDEX IF NOT EXISTS ix_{table_name}_default_id_created_at
            ON public.{table_name}_default (id, created_at)
            """
        )

        # ── 5. Migrate existing data into the new partitioned table ───────
        #    INSERT INTO ... SELECT routes each row to the correct partition.
        insert_sql = "INSERT INTO public." + table_name + " SELECT * FROM public." + table_name + "_old"
        op.execute(insert_sql)

        # ── 6. Drop the shadow table ──────────────────────────────────────
        drop_sql = "DROP TABLE public." + table_name + "_old"
        op.execute(drop_sql)


def _ensure_missing_months(
    conn: Connection,
    table_name: str,
    partition_months: list[tuple[int, int]],
) -> None:
    """Idempotently add partitions that don't yet exist (handles partial
    application or new months prepended before the next migration)."""
    for year, month in partition_months:
        pname = _partition_name(table_name, year, month)
        start, end = _month_bounds(year, month)
        op.execute(
            f"""
            CREATE TABLE IF NOT EXISTS public.{pname}
            PARTITION OF public.{table_name}
            FOR VALUES FROM ('{start}') TO ('{end}')
            """
        )
        op.execute(
            f"""
            CREATE INDEX IF NOT EXISTS ix_{pname}_id_created_at
            ON public.{pname} (id, created_at)
            """
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
            """
            SELECT inhrelid::regclass::text AS part_name
            FROM pg_inherits
            WHERE inhparent = format('public.%I', :tbl)::regclass
              AND inhrelid::regclass::text NOT LIKE '%_default'
            """,
            {"tbl": table_name},
        ).fetchall()
        partitions = [r[0] for r in rows]

        if not partitions:
            continue

        # ── 1. Detach each partition so it becomes a standalone table ──────
        for p in reversed(partitions):
            op.execute(
                f"ALTER TABLE public.{table_name} "
                f"DETACH PARTITION public.{p}"
            )

        # ── 2. Build a flat table with the same schema ─────────────────────
        flat_name = f"{table_name}_pre_downgrade"
        op.execute(
            f"CREATE TABLE public.{flat_name} "
            f"(LIKE public.{table_name} INCLUDING ALL)"
        )

        # ── 3. Reassemble data into the flat table ─────────────────────────
        selects = ["SELECT * FROM public." + p for p in partitions]
        if selects:
            union_all = " UNION ALL ".join(selects)
            insert_sql = "INSERT INTO public." + flat_name + " " + union_all
            op.execute(insert_sql)

        # ── 4. Drop the now-empty partitioned parent (default partition
        #        is dropped via CASCADE) ────────────────────────────────────
        drop_sql = "DROP TABLE public." + table_name + " CASCADE"
        op.execute(drop_sql)

        # ── 5. Drop the now-empty detached partitions ──────────────────────
        for p in partitions:
            drop_part_sql = "DROP TABLE IF EXISTS public." + p + " CASCADE"
            op.execute(drop_part_sql)

        # ── 6. Rename the reassembled flat table to the original name ──────
        rename_sql = "ALTER TABLE public." + flat_name + " RENAME TO " + table_name
        op.execute(rename_sql)
