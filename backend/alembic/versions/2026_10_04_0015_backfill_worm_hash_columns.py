"""backfill worm_hash columns from audit_logs.details

Populate ``audit.audit_logs.worm_hash`` and ``audit.audit_logs.worm_prev_hash``
for rows that were sealed before the ORM mapped those columns. Existing rows
carry the seal inside the ``details`` JSONB payload; this migration copies the
values into the dedicated columns so the read path can serve both pre- and
post-backfill rows.

Idempotent: re-running upgrade() on an already-backfilled table is safe
because rows whose ``worm_hash`` is already populated are skipped by the
``WHERE worm_hash IS NULL`` guard.

Revision ID: 20261004_0015_backfill_worm_hash_columns
Revises: 20261004_0014_encrypt_payment_gateway_credentials
Create Date: 2026-10-04 10:00:00
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


revision: str = "20261004_0015_backfill_worm_hash_columns"
down_revision: Union[str, None] = "20261004_0014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    offline = _is_offline(bind)
    if offline:
        return
    inspector = sa.inspect(bind)
    if "audit_logs" not in inspector.get_table_names(schema="audit"):
        return
    existing = {c["name"] for c in inspector.get_columns("audit_logs", schema="audit")}
    if "worm_hash" not in existing or "worm_prev_hash" not in existing:
        return

    conn = bind.connect()
    try:
        conn.execute(
            sa.text("""
                UPDATE audit.audit_logs
                SET worm_hash = COALESCE(details->>'worm_hash', worm_hash),
                    worm_prev_hash = COALESCE(details->>'worm_prev_hash', worm_prev_hash)
                WHERE worm_hash IS NULL
                  AND details IS NOT NULL
                  AND details ? 'worm_hash'
            """)
        )
        conn.commit()
    finally:
        conn.close()


def downgrade() -> None:
    bind = op.get_bind()
    offline = _is_offline(bind)
    if offline:
        return
    inspector = sa.inspect(bind)
    if "audit_logs" not in inspector.get_table_names(schema="audit"):
        return
    existing = {c["name"] for c in inspector.get_columns("audit_logs", schema="audit")}
    if "worm_hash" in existing:
        conn = bind.connect()
        try:
            conn.execute(
                sa.text("""
                    UPDATE audit.audit_logs
                    SET worm_hash = NULL,
                        worm_prev_hash = NULL
                    WHERE details IS NOT NULL
                      AND details ? 'worm_hash'
                """)
            )
            conn.commit()
        finally:
            conn.close()
