"""Phase 5B: adopt_mixins_in_5_domains (comms, hr, security, country, promotions)

This migration back-fills the canonical mixin columns onto every table in the
5 target domains that is missing one or more of:

    - created_at
    - updated_at
    - is_deleted
    - country_code
    - version

The application side (see ``domains/_mixin_compliance.py``) appends these
columns to ``Base.metadata`` at import time so the ORM sees the same
contract. The migration makes the deployed database converge with the model
metadata so the live schema satisfies the same architectural laws (Law 23,
45, 50, 51, 52, 53) referenced by ``tests/architecture/test_mixin_adoption.py``.

The migration is a **no-op when run on a fresh database** that has been
created from the patched metadata (since the columns are already there),
and is **idempotent on an existing database** because each ``safe_add_column``
call checks for column existence before issuing ``ALTER TABLE``.

Schemas covered: comms, hr, security, country, promotions.
Skipped on SQLite (the test/dev dialect rebuilds from ORM metadata).
"""
from __future__ import annotations

import os
import sys
from typing import Sequence, Union

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.exc import NoInspectionAvailable

from migration_helpers import safe_add_column

revision: str = "2026_09_04_0001"
down_revision: Union[str, None] = "2026_09_03_0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TARGET_SCHEMAS = ("comms", "hr", "security", "country", "promotions")


def _is_offline(conn) -> bool:
    if conn is None:
        return True
    try:
        sa_inspect(conn)
        return False
    except (NoInspectionAvailable, Exception):
        return True


def _column_for(name: str) -> sa.Column:
    if name == "created_at":
        return sa.Column(
            "created_at", sa.DateTime(),
            server_default=sa.func.now(), nullable=False, index=True,
        )
    if name == "updated_at":
        return sa.Column(
            "updated_at", sa.DateTime(),
            server_default=sa.func.now(),
            onupdate=sa.func.now(), nullable=False,
        )
    if name == "is_deleted":
        return sa.Column(
            "is_deleted", sa.Boolean(),
            nullable=False, server_default=sa.text("false"), index=True,
        )
    if name == "country_code":
        return sa.Column(
            "country_code", sa.String(2),
            nullable=True, index=True,
        )
    if name == "version":
        return sa.Column(
            "version", sa.Integer(),
            nullable=False, server_default=sa.text("1"),
        )
    raise ValueError(f"Unknown mixin column: {name}")


def _iter_target_tables(conn):
    """Yield (schema, table) for every table in TARGET_SCHEMAS that
    currently exists in the database.
    """
    import infrastructure.database.base as models
    if _is_offline(conn):
        for table in models.Base.metadata.tables.values():
            schema = (table.schema or "").lower()
            if schema not in TARGET_SCHEMAS:
                continue
            yield table.schema, table
        return
    inspector = sa_inspect(conn)
    for table in models.Base.metadata.tables.values():
        schema = (table.schema or "").lower()
        if schema not in TARGET_SCHEMAS:
            continue
        if not inspector.has_table(table.name, schema=table.schema):
            continue
        yield table.schema, table


def upgrade() -> None:
    conn = op.get_bind()
    if not _is_offline(conn) and conn.dialect.name == "sqlite":
        return
    for schema, table in _iter_target_tables(conn):
        existing = {c["name"] for c in sa_inspect(conn).get_columns(table.name, schema=schema)}
        for col_name in ("created_at", "updated_at", "is_deleted", "country_code", "version"):
            if col_name in existing:
                continue
            safe_add_column(op, table.name, _column_for(col_name), schema=schema)


def downgrade() -> None:
    from migration_helpers import safe_drop_column
    conn = op.get_bind()
    if not _is_offline(conn) and conn.dialect.name == "sqlite":
        return
    for schema, table in _iter_target_tables(conn):
        for col_name in ("version", "country_code", "is_deleted", "updated_at", "created_at"):
            safe_drop_column(op, table.name, col_name, schema=schema)
