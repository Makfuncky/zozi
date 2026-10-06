"""add WORM hash columns to audit.audit_logs

Adds ``worm_hash`` and ``worm_prev_hash`` to ``audit.audit_logs`` so the
Write-Once-Read-Many (WORM) audit service can build and verify a tamper-evident
chain without mutating the row after insert (which would violate WORM).

This is a no-op on SQLite because the column will be added by ``Base.metadata``
on next ORM ``create_all``; the Alembic op is still emitted so production
Postgres gets the column deterministically.

Revision ID: 20260827_audit_logs_worm_hash
Revises: 20260823_governance_out_of_audit_schema
Create Date: 2026-08-27 02:30:00
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.exc import NoInspectionAvailable

revision: str = "20260827_audit_logs_worm_hash"
down_revision: Union[str, None] = "20260823_governance_out_of_audit_schema"
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


def upgrade() -> None:
    bind = op.get_bind()
    offline = _is_offline(bind)
    if offline:
        op.add_column(
            "worm_hash",
            sa.Column("worm_hash", sa.String(length=128), nullable=True),
            schema="audit",
        )
        op.create_index(
            "ix_audit_audit_logs_worm_hash",
            "audit_logs",
            ["worm_hash"],
            schema="audit",
        )
        op.add_column(
            "worm_prev_hash",
            sa.Column("worm_prev_hash", sa.String(length=128), nullable=True),
            schema="audit",
        )
        op.create_index(
            "ix_audit_audit_logs_worm_prev_hash",
            "audit_logs",
            ["worm_prev_hash"],
            schema="audit",
        )
        return
    inspector = sa_inspect(bind)
    if "audit_logs" not in inspector.get_table_names(schema="audit"):
        return
    existing = {c["name"] for c in inspector.get_columns("audit_logs", schema="audit")}
    if "worm_hash" not in existing:
        op.add_column(
            "worm_hash",
            sa.Column("worm_hash", sa.String(length=128), nullable=True),
            schema="audit",
        )
        op.create_index(
            "ix_audit_audit_logs_worm_hash",
            "audit_logs",
            ["worm_hash"],
            schema="audit",
        )
    if "worm_prev_hash" not in existing:
        op.add_column(
            "worm_prev_hash",
            sa.Column("worm_prev_hash", sa.String(length=128), nullable=True),
            schema="audit",
        )
        op.create_index(
            "ix_audit_audit_logs_worm_prev_hash",
            "audit_logs",
            ["worm_prev_hash"],
            schema="audit",
        )


def downgrade() -> None:
    bind = op.get_bind()
    offline = _is_offline(bind)
    if offline:
        op.drop_column("audit_logs", "worm_prev_hash", schema="audit")
        op.drop_index(
            "ix_audit_audit_logs_worm_prev_hash",
            table_name="audit_logs",
            schema="audit",
        )
        op.drop_column("audit_logs", "worm_hash", schema="audit")
        op.drop_index(
            "ix_audit_audit_logs_worm_hash",
            table_name="audit_logs",
            schema="audit",
        )
        return
    inspector = sa_inspect(bind)
    if "audit_logs" not in inspector.get_table_names(schema="audit"):
        return
    existing = {c["name"] for c in inspector.get_columns("audit_logs", schema="audit")}
    if "worm_prev_hash" in existing:
        op.drop_column("audit_logs", "worm_prev_hash", schema="audit")
        op.drop_index(
            "ix_audit_audit_logs_worm_prev_hash",
            table_name="audit_logs",
            schema="audit",
        )
    if "worm_hash" in existing:
        op.drop_index(
            "ix_audit_audit_logs_worm_hash",
            table_name="audit_logs",
            schema="audit",
        )
        op.drop_column("audit_logs", "worm_hash", schema="audit")
