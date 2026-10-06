"""Shared, idempotent Alembic helpers for ZOZI migrations.

These protect ``alembic upgrade`` / ``alembic downgrade`` from crashing when a
column or index already exists (re-run migrations, partially applied schemas,
or schema drift). They honour an explicit PostgreSQL ``schema`` when provided.

In offline (``--sql``) mode catalog introspection is unavailable, so helpers
refuse to fabricate an answer.  Callers should treat that as "the object is
missing" and emit the DDL unconditionally.
"""
from __future__ import annotations

from typing import Optional, Sequence

from sqlalchemy import inspect
from sqlalchemy.exc import NoInspectionAvailable


def _is_offline(bind) -> bool:
    """Return True when running in alembic --sql offline mode."""
    if bind is None:
        return True
    try:
        inspect(bind)
        return False
    except (NoInspectionAvailable, Exception):
        return True


def _bind(op):
    return op.get_bind()


def safe_add_column(op, table: str, column, schema: Optional[str] = None) -> None:
    """Add ``column`` to ``table`` only if it does not already exist."""
    bind = _bind(op)
    if _is_offline(bind):
        op.add_column(table, column, schema=schema)
        return
    inspector = inspect(bind)
    existing = {c["name"] for c in inspector.get_columns(table, schema=schema)}
    name = column.name if hasattr(column, "name") else column
    if name in existing:
        return
    op.add_column(table, column, schema=schema)


def safe_drop_column(op, table: str, column_name: str, schema: Optional[str] = None) -> None:
    """Drop ``column_name`` from ``table`` only if it exists."""
    bind = _bind(op)
    if _is_offline(bind):
        op.drop_column(table, column_name, schema=schema)
        return
    inspector = inspect(bind)
    existing = {c["name"] for c in inspector.get_columns(table, schema=schema)}
    if column_name not in existing:
        return
    op.drop_column(table, column_name, schema=schema)


def safe_create_index(
    op,
    index_name: str,
    table: str,
    columns: Sequence[str],
    schema: Optional[str] = None,
    postgresql_using: Optional[str] = None,
    unique: bool = False,
) -> None:
    """Create ``index_name`` on ``table(columns)`` only if it does not exist."""
    bind = _bind(op)
    if _is_offline(bind):
        op.create_index(
            index_name,
            table,
            list(columns),
            schema=schema,
            postgresql_using=postgresql_using,
            unique=unique,
        )
        return
    inspector = inspect(bind)
    existing = {i["name"] for i in inspector.get_indexes(table, schema=schema)}
    if index_name in existing:
        return
    op.create_index(
        index_name,
        table,
        list(columns),
        schema=schema,
        postgresql_using=postgresql_using,
        unique=unique,
    )


def safe_drop_index(op, index_name: str, table: str, schema: Optional[str] = None) -> None:
    """Drop ``index_name`` on ``table`` only if it exists."""
    bind = _bind(op)
    if _is_offline(bind):
        op.drop_index(index_name, table_name=table, schema=schema)
        return
    inspector = inspect(bind)
    existing = {i["name"] for i in inspector.get_indexes(table, schema=schema)}
    if index_name not in existing:
        return
    op.drop_index(index_name, table_name=table, schema=schema)
