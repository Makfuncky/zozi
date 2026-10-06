"""add audit.audit_logs.version (mixin-compliance column)

domains/_mixin_compliance.py force-appends the five mixin columns
(created_at, updated_at, is_deleted, country_code, version) onto every domain
table at import time, but no migration had ever created `version` on
`audit.audit_logs`. Because every login writes an audit-log row, every
/api/v1/auth/login request failed with:

    psycopg2.errors.UndefinedColumn: column "version" of relation
    "audit_logs" does not exist

This adds the missing column so the ORM and the database agree.

Revision ID: 20261003_0012
Revises: 20261003_0011
"""
from __future__ import annotations

import sys
from pathlib import Path

import sqlalchemy as sa
from alembic import op

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from migration_helpers import safe_add_column  # noqa: E402

revision: str = "20261003_0012"
down_revision: str | None = "20261003_0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    safe_add_column(
        op,
        "audit_logs",
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        schema="audit",
    )


def downgrade() -> None:
    op.drop_column("audit_logs", "version", schema="audit")