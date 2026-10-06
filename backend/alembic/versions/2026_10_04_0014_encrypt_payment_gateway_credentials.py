"""expand-contract migration: encrypt payment_gateway_connections.secret_key and webhook_secret

Law 275: AES-256-GCM encryption at rest for sensitive DB fields.
Law 313: PCI-DSS — Admin-entered API keys are AES-256 encrypted at rest.
§10.1 Key Rule 1: Payment gateway API keys and webhook secrets are NEVER stored in plain text.

Expand phase:
  1. Add secret_key_enc (TEXT, nullable) and webhook_secret_enc (TEXT, nullable).
  2. Backfill: encrypt existing plaintext values into the new columns using
     the same FieldEncryptor the ORM will use at runtime.  Rows that already
     carry the enc:: prefix (idempotent re-run) are left untouched.
  3. Drop the old plaintext columns.
  4. Rename the encrypted columns to their final names.

Downgrade reverses each step in order.

Idempotent: re-running upgrade() on an already-converted table is safe
because re-encrypting an enc::-prefixed value returns it unchanged
(FieldEncryptor.encrypt is a no-op for values that already start with enc::).

Dependencies: 20261004_0013 (current head)
"""
from __future__ import annotations

import os
import sys

# The migration runs inside alembic/ which is on sys.path (prepend_sys_path in
# alembic.ini).  Add backend/ so we can import infrastructure modules.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect as sa_inspect, text
from sqlalchemy.exc import NoInspectionAvailable

revision: str = "20261004_0014"
down_revision: str | None = "20261004_0013"
branch_labels = None
depends_on = None

_SCHEMA = "finance"
_TABLE = "payment_gateway_connections"
_COL_SK = "secret_key"
_COL_WH = "webhook_secret"
_COL_SK_NEW = "secret_key_enc"
_COL_WH_NEW = "webhook_secret_enc"


def _is_offline(conn) -> bool:
    """Return True when running in alembic --sql offline mode."""
    if conn is None:
        return True
    try:
        sa_inspect(conn)
        return False
    except (NoInspectionAvailable, Exception):
        return True


def _encrypt(value):
    """Encrypt a value; return None unchanged."""
    if value is None:
        return None
    return field_encryptor.encrypt(value)


def upgrade() -> None:
    conn = op.get_bind()
    offline = _is_offline(conn)

    # ── Phase 1: expand — add new encrypted columns ────────────────────────
    op.add_column(
        _TABLE,
        sa.Column(_COL_SK_NEW, sa.Text(), nullable=True),
        schema=_SCHEMA,
    )
    op.add_column(
        _TABLE,
        sa.Column(_COL_WH_NEW, sa.Text(), nullable=True),
        schema=_SCHEMA,
    )

    # ── Phase 2: backfill — encrypt existing plaintext values ──────────────
    # In offline mode we cannot SELECT/UPDATE data, so skip the backfill.
    if not offline:
        rows = conn.execute(
            sa.text(
                f"SELECT id, {_COL_SK}, {_COL_WH} "
                f"FROM {_SCHEMA}.{_TABLE} "
                f"WHERE id IS NOT NULL"
            )
        ).fetchall()

        for row in rows:
            row_id = row[0]
            plain_sk = row[1]
            plain_wh = row[2]
            enc_sk = _encrypt(plain_sk)
            enc_wh = _encrypt(plain_wh)
            conn.execute(
                sa.text(
                    f"UPDATE {_SCHEMA}.{_TABLE} "
                    f"SET {_COL_SK_NEW} = :sk, {_COL_WH_NEW} = :wh "
                    f"WHERE id = :id"
                ),
                {"sk": enc_sk, "wh": enc_wh, "id": row_id},
            )

    # ── Phase 3: contract — drop old plaintext columns ─────────────────────
    op.drop_column(_TABLE, _COL_SK, schema=_SCHEMA)
    op.drop_column(_TABLE, _COL_WH, schema=_SCHEMA)

    # ── Phase 4: rename encrypted columns to their final names ─────────────
    op.alter_column(
        _TABLE,
        _COL_SK_NEW,
        new_column_name=_COL_SK,
        schema=_SCHEMA,
    )
    op.alter_column(
        _TABLE,
        _COL_WH_NEW,
        new_column_name=_COL_WH,
        schema=_SCHEMA,
    )


def downgrade() -> None:
    conn = op.get_bind()
    offline = _is_offline(conn)

    # ── Reverse rename: secret_key → secret_key_enc ────────────────────────
    op.alter_column(
        _TABLE,
        _COL_SK,
        new_column_name=_COL_SK_NEW,
        schema=_SCHEMA,
    )
    op.alter_column(
        _TABLE,
        _COL_WH,
        new_column_name=_COL_WH_NEW,
        schema=_SCHEMA,
    )

    # ── Re-add plaintext columns ───────────────────────────────────────────
    op.add_column(
        _TABLE,
        sa.Column(_COL_SK, sa.String(1000), nullable=True),
        schema=_SCHEMA,
    )
    op.add_column(
        _TABLE,
        sa.Column(_COL_WH, sa.String(1000), nullable=True),
        schema=_SCHEMA,
    )

    # ── Backfill plaintext from encrypted columns ──────────────────────────
    # In offline mode we cannot SELECT/UPDATE data, so skip the backfill.
    if not offline:
        rows = conn.execute(
            sa.text(
                f"SELECT id, {_COL_SK_NEW}, {_COL_WH_NEW} "
                f"FROM {_SCHEMA}.{_TABLE} "
                f"WHERE id IS NOT NULL"
            )
        ).fetchall()

        for row in rows:
            row_id = row[0]
            enc_sk = row[1]
            enc_wh = row[2]
            plain_sk = field_encryptor.decrypt(enc_sk) if enc_sk else None
            plain_wh = field_encryptor.decrypt(enc_wh) if enc_wh else None
            conn.execute(
                sa.text(
                    f"UPDATE {_SCHEMA}.{_TABLE} "
                    f"SET {_COL_SK} = :sk, {_COL_WH} = :wh "
                    f"WHERE id = :id"
                ),
                {"sk": plain_sk, "wh": plain_wh, "id": row_id},
            )

    # ── Drop encrypted columns ─────────────────────────────────────────────
    op.drop_column(_TABLE, _COL_SK_NEW, schema=_SCHEMA)
    op.drop_column(_TABLE, _COL_WH_NEW, schema=_SCHEMA)
