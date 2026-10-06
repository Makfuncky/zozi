"""dba03_version_column_backfill

Revision ID: 20260806_0005
Revises: 20260806_0004
Create Date: 2026-08-06

DBA03 remediation, part 2: the canonical ``Base`` already provides the audit
columns (created_at/updated_at/created_by/updated_by, is_deleted/deleted_at,
uuid) and ``TenantMixin`` provides country/uuid/is_active.  The remaining gap
across ~90 tables was the optimistic-lock ``version`` column, which is now
supplied by ``VersionMixin`` on the affected models.

This migration backfills ``version`` on every deployed table that does not yet
have it, so existing databases (PostgreSQL) converge with the models.  It is
idempotent (``safe_add_column`` no-ops when the column already exists) and is
skipped on SQLite, where the dev/test schema is rebuilt from the ORM metadata.

``models`` is imported lazily inside the helpers so this revision module imports
cleanly even in tooling contexts that validate migrations in isolation.
"""
from __future__ import annotations
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.exc import NoInspectionAvailable

from migration_helpers import safe_add_column, safe_drop_column


revision: str = "20260806_0005"
down_revision: Union[str, None] = "20260806_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _is_offline(conn) -> bool:
    """Return True when running in alembic --sql offline mode."""
    if conn is None:
        return True
    try:
        sa_inspect(conn)
        return False
    except (NoInspectionAvailable, Exception):
        return True


def _version_column() -> sa.Column:
    return sa.Column(
        "version",
        sa.Integer(),
        nullable=False,
        server_default=sa.text("1"),
    )


def _iter_deployed_tables(conn):
    import infrastructure.database.base as models  # local import: keeps this revision importable in isolation
    if _is_offline(conn):
        # In offline mode we cannot introspect the catalog, so we yield every
        # ORM table and let safe_add_column emit DDL unconditionally.
        for table in models.Base.metadata.tables.values():
            yield table.schema, table.name
        return
    inspector = sa_inspect(conn)
    for table in models.Base.metadata.tables.values():
        schema = table.schema
        name = table.name
        if inspector.has_table(name, schema=schema):
            yield schema, name


def upgrade() -> None:
    conn = op.get_bind()
    if not _is_offline(conn) and conn.dialect.name == "sqlite":
        return
    for schema, name in _iter_deployed_tables(conn):
        safe_add_column(op, name, _version_column(), schema=schema)


def downgrade() -> None:
    conn = op.get_bind()
    if not _is_offline(conn) and conn.dialect.name == "sqlite":
        return
    for schema, name in _iter_deployed_tables(conn):
        safe_drop_column(op, name, "version", schema=schema)
