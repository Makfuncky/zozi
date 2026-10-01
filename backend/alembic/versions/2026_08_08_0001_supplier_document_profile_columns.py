"""supplier_document_profile_columns

Revision ID: 20260808_0001
Revises: 20260806_0007
Create Date: 2026-08-08

Adds the columns the supplier-documents feature and supplier-profile updates
actually read/write, which were missing from the ORM models:

``supplier.supplier_documents`` (SupplierDocument):
  - document_name   (String 255)
  - status          (String 30, default 'pending')
  - expires_at      (DateTime)
  - review_note     (Text)
  - reviewed_by     (Integer)
  - reviewed_at     (DateTime)

``supplier.supplier_profiles`` (SupplierProfile):
  - address         (String 255)
  - website         (String 255)
  - bio             (Text)
  - about_us        (Text)
  - business_type   (String 50)
  - verified_documents (Text, JSON-encoded list)

These back ``services.supplier.suppliers_write_service`` and the supplier-document /
supplier-profile controllers. Without them the endpoints raise AttributeError /
TypeError at runtime.

Skipped on SQLite: the dev/test schema is rebuilt from the ORM metadata via the
build step in ``alembic/env.py``, so the models alone drive the SQLite schema.
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from alembic.migration_helpers import safe_add_column, safe_drop_column


revision: str = "20260808_0001"
down_revision: Union[str, None] = "20260806_0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_DOCUMENT_COLUMNS = [
    ("document_name", sa.String(255), {"nullable": True}),
    ("status", sa.String(30), {"nullable": True, "server_default": sa.text("'pending'")}),
    ("expires_at", sa.DateTime(timezone=True), {"nullable": True}),
    ("review_note", sa.Text(), {"nullable": True}),
    ("reviewed_by", sa.Integer(), {"nullable": True}),
    ("reviewed_at", sa.DateTime(timezone=True), {"nullable": True}),
]

_PROFILE_COLUMNS = [
    ("address", sa.String(255), {"nullable": True}),
    ("website", sa.String(255), {"nullable": True}),
    ("bio", sa.Text(), {"nullable": True}),
    ("about_us", sa.Text(), {"nullable": True}),
    ("business_type", sa.String(50), {"nullable": True}),
    ("verified_documents", sa.Text(), {"nullable": True}),
]


def _add_columns(op, schema: str, table: str, specs) -> None:
    for name, col_type, kw in specs:
        safe_add_column(op, table, sa.Column(name, col_type, **kw), schema=schema)


def _drop_columns(op, schema: str, table: str, specs) -> None:
    for name, _, _ in reversed(specs):
        safe_drop_column(op, table, name, schema=schema)


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        return

    _add_columns(op, "supplier", "supplier_documents", _DOCUMENT_COLUMNS)
    _add_columns(op, "supplier", "supplier_profiles", _PROFILE_COLUMNS)


def downgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        return

    _drop_columns(op, "supplier", "supplier_profiles", _PROFILE_COLUMNS)
    _drop_columns(op, "supplier", "supplier_documents", _DOCUMENT_COLUMNS)
