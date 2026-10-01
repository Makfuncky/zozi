"""catalog_categories_dba03_audit_softdelete

Revision ID: 20260806_0004
Revises: 20260806_0003
Create Date: 2026-08-06

Brings ``commerce.categories`` in line with the mandatory column contract (DBA03)
using the non-colliding mixin composition ``TenantMixin + CreatedByMixin +
SoftDeleteMixin`` (the model already defined its own ``created_at`` /
``updated_at``, so those are left untouched to avoid a duplicate-column clash):

  - commerce.categories gains created_by / updated_by (CreatedByMixin)
  - commerce.categories gains is_deleted / deleted_at / deleted_by /
    delete_reason (SoftDeleteMixin)

Idempotent and skipped on SQLite: the dev/test database is recreated from the
ORM metadata via the build step in ``alembic/env.py``, so the model changes
alone drive the SQLite schema.
"""
from __future__ import annotations
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

from alembic.migration_helpers import safe_add_column, safe_drop_column


revision: str = "20260806_0004"
down_revision: Union[str, None] = "20260806_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _categories_columns() -> list:
    return [
        sa.Column("created_by", sa.Integer(), nullable=True, index=True),
        sa.Column("updated_by", sa.Integer(), nullable=True, index=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false(), index=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.Integer(), nullable=True),
        sa.Column("delete_reason", sa.Text(), nullable=True),
    ]


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        return
    for col in _categories_columns():
        safe_add_column(op, "categories", col, schema="commerce")


def downgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        return
    for col in reversed(_categories_columns()):
        safe_drop_column(op, "categories", col.name, schema="commerce")