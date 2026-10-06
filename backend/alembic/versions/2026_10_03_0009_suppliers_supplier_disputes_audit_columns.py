"""suppliers_supplier_disputes_audit_columns

Resolves FILE 104 findings TF-266 and TF-267 on
``backend/domains/suppliers/models/suppliers.py``.

The ORM class ``SupplierDispute`` (``suppliers.py:263``) declares both audit
columns that Law 23 / Law 54 require:

  - ``updated_at = Column(DateTime, server_default=func.now(),
    onupdate=func.now(), nullable=True)``   -> Law 23 (audit columns)
  - ``is_deleted = Column(Boolean, default=False, server_default='false',
    nullable=False, index=True)``           -> Law 54 (soft delete)

but the applied schema in ``information_schema.columns`` carried NEITHER.
Because Law 6 makes Alembic the single source of truth for schema, the
database was the side that had to move: the ORM was already correct, and any
``SELECT`` built from ``SupplierDispute`` emits ``updated_at`` and
``is_deleted`` in its column list, so every read of the table raised
``UndefinedColumn`` against the drifted schema.

This migration is expand-only (Law 57): it adds two columns and one index,
leaves all existing rows intact, and does not drop or rewrite anything.

Skipped on SQLite: dev/test databases are recreated from ORM metadata
(``infrastructure/database/init_db.py``), which already carries both columns.
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


def _is_offline(conn) -> bool:
    if conn is None:
        return True
    try:
        from sqlalchemy import inspect as sa_inspect
        from sqlalchemy.exc import NoInspectionAvailable
        sa_inspect(conn)
        return False
    except (NoInspectionAvailable, Exception):
        return True


revision: str = "20261003_0009"
down_revision: Union[str, None] = "20261001_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "suppliers"
TABLE = "supplier_disputes"
IS_DELETED_INDEX = "ix_suppliers_supplier_disputes_is_deleted"


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        return

    offline = _is_offline(bind)
    if offline:
        return
    inspector = sa.inspect(bind)
    if TABLE not in inspector.get_table_names(schema=SCHEMA):
        return

    existing = {
        c["name"] for c in inspector.get_columns(TABLE, schema=SCHEMA)
    }

    # TF-266 - Law 23: the ORM already selects updated_at, the schema must have it.
    if "updated_at" not in existing:
        op.add_column(
            TABLE,
            sa.Column(
                "updated_at",
                sa.DateTime(),
                nullable=True,
                server_default=sa.func.now(),
            ),
            schema=SCHEMA,
        )

    # TF-267 - Law 54: soft-delete flag, boolean, default false.
    if "is_deleted" not in existing:
        op.add_column(
            TABLE,
            sa.Column(
                "is_deleted",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            ),
            schema=SCHEMA,
        )

    existing_indexes = {
        ix["name"]
        for ix in inspector.get_indexes(TABLE, schema=SCHEMA)
        if ix.get("name")
    }
    if IS_DELETED_INDEX not in existing_indexes:
        op.create_index(
            IS_DELETED_INDEX,
            TABLE,
            ["is_deleted"],
            unique=False,
            schema=SCHEMA,
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        return

    offline = _is_offline(bind)
    if offline:
        return
    inspector = sa.inspect(bind)
    if TABLE not in inspector.get_table_names(schema=SCHEMA):
        return

    existing_indexes = {
        ix["name"]
        for ix in inspector.get_indexes(TABLE, schema=SCHEMA)
        if ix.get("name")
    }
    if IS_DELETED_INDEX in existing_indexes:
        op.drop_index(IS_DELETED_INDEX, table_name=TABLE, schema=SCHEMA)

    existing = {
        c["name"] for c in inspector.get_columns(TABLE, schema=SCHEMA)
    }
    if "is_deleted" in existing:
        op.drop_column(TABLE, "is_deleted", schema=SCHEMA)
    if "updated_at" in existing:
        op.drop_column(TABLE, "updated_at", schema=SCHEMA)
