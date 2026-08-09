"""Shared, idempotent Alembic helpers for ZOZI migrations.

These protect ``alembic upgrade`` / ``alembic downgrade`` from crashing when a
column or index already exists (re-run migrations, partially applied schemas,
or schema drift). They honour an explicit PostgreSQL ``schema`` when provided.

Imported by migrations as ``from migration_helpers import ...``; ``alembic/env.py``
puts ``backend/`` on ``sys.path`` so this module resolves at the backend root.
"""
from __future__ import annotations

from typing import Optional, Sequence

from sqlalchemy import inspect


def _bind(op):
    return op.get_bind()


def safe_add_column(op, table: str, column, schema: Optional[str] = None) -> None:
    """Add ``column`` to ``table`` only if it does not already exist."""
    bind = _bind(op)
    inspector = inspect(bind)
    existing = {c["name"] for c in inspector.get_columns(table, schema=schema)}
    name = column.name if hasattr(column, "name") else column
    if name in existing:
        return
    op.add_column(table, column, schema=schema)


def safe_drop_column(op, table: str, column_name: str, schema: Optional[str] = None) -> None:
    """Drop ``column_name`` from ``table`` only if it exists."""
    bind = _bind(op)
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
    inspector = inspect(bind)
    existing = {i["name"] for i in inspector.get_indexes(table, schema=schema)}
    if index_name not in existing:
        return
    op.drop_index(index_name, table=table, schema=schema)
