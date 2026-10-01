"""rename_return_deadline_to_return_deadline_at

Revision ID: 20260805_0001
Revises: 20260801_0018
Create Date: 2026-08-05

Renames commerce.return_requests.return_deadline -> return_deadline_at to follow
the datetime naming convention (DB11). Idempotent and skipped on SQLite (dev DB is
recreated via metadata.create_all).
"""
from __future__ import annotations
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


revision: str = "20260805_0001"
down_revision: Union[str, None] = "20260801_0018"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        return
    conn.execute(
        text(
            'ALTER TABLE IF EXISTS commerce.return_requests '
            'RENAME COLUMN return_deadline TO return_deadline_at'
        )
    )


def downgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        return
    conn.execute(
        text(
            'ALTER TABLE IF EXISTS commerce.return_requests '
            'RENAME COLUMN return_deadline_at TO return_deadline'
        )
    )
