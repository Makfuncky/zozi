"""add audit.audit_logs worm-hash seal columns

The AuditLog ORM model maps ``worm_hash`` / ``worm_prev_hash`` (String(128),
nullable) and every login writes an audit row, so /auth/login failed with:

    psycopg2.errors.UndefinedColumn: column "worm_hash" of relation
    "audit_logs" does not exist

Revision 20261004_0015_backfill_worm_hash_columns only *backfills* these columns
and returns early when they are absent -- nothing ever created them.

Revision ID: 20261004_0017
Revises: 20261004_0016_encrypt_mfa_factor_secret
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from migration_helpers import safe_add_column  # noqa: E402

revision: str = "20261004_0017"
down_revision: Union[str, None] = "20261004_0016_encrypt_mfa_factor_secret"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    safe_add_column(
        op,
        "audit_logs",
        sa.Column("worm_hash", sa.String(length=128), nullable=True),
        schema="audit",
    )
    safe_add_column(
        op,
        "audit_logs",
        sa.Column("worm_prev_hash", sa.String(length=128), nullable=True),
        schema="audit",
    )


def downgrade() -> None:
    op.drop_column("audit_logs", "worm_prev_hash", schema="audit")
    op.drop_column("audit_logs", "worm_hash", schema="audit")