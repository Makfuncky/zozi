"""create accounts.mfa_factors table and align secret type

The ORM model ``MfaFactor`` (``domains/accounts/models/mfa_factor.py``) maps
``accounts.mfa_factors`` but no migration in the chain ever created the table.
Production databases have it because dev/test bootstrap uses ``create_all``, but a
database built purely from ``alembic upgrade head`` would be missing it.

This revision also reconciles the ``secret`` column type.  Migration
``20261004_0016_encrypt_mfa_factor_secret`` widened it to ``String(1024)`` while
the ORM still declares ``EncryptedString(512)``.  ``EncryptedString`` is a
``TypeDecorator`` whose ``impl`` is ``Text``; with ``field_encryptor`` active it
renders as ``String(_encrypted_storage_length(512))``.  To keep the migration chain
authoritative and avoid a type mismatch with the ORM, this revision sets the column
to ``Text`` (the TypeDecorator impl), which can store any ciphertext length.

Idempotent: every step guards on table/column presence so re-running is safe.

Revision ID: 20261004_0020_create_mfa_factors_and_align_secret
Revises: 20261004_0019_add_products_currency
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from migration_helpers import safe_add_column  # noqa: E402

logger = logging.getLogger("alembic.runtime.migration")


revision: str = "20261004_0020_create_mfa_factors_and_align_secret"
down_revision: Union[str, None] = "20261004_0019_add_products_currency"
branch_labels: Union[Sequence[str], None] = None
depends_on: Union[Sequence[str], None] = None


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


def _has_table(bind, table: str, schema: str) -> bool:
    inspector = sa.inspect(bind)
    return table in inspector.get_table_names(schema=schema)


def _has_column(bind, table: str, column: str, schema: str) -> bool:
    inspector = sa.inspect(bind)
    try:
        return column in {c["name"] for c in inspector.get_columns(table, schema=schema)}
    except sa.exc.NoSuchTableError:
        return False


def upgrade() -> None:
    bind = op.get_bind()
    if _is_offline(bind):
        return
    if bind.dialect.name == "sqlite":
        return

    if not _has_table(bind, "mfa_factors", "accounts"):
        op.create_table(
            "mfa_factors",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("factor_type", sa.String(length=20), nullable=False),
            sa.Column("secret", sa.Text(), nullable=False),
            sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("backup_codes", sa.JSON(), nullable=True),
            sa.Column("country_code", sa.String(length=2), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True, server_default=sa.func.now()),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.ForeignKeyConstraint(["user_id"], ["accounts.users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.Index("ix_mfa_factors_user_id", "user_id"),
            schema="accounts",
        )
    else:
        existing = {c["name"] for c in sa.inspect(bind).get_columns("mfa_factors", schema="accounts")}
        if "version" not in existing:
            safe_add_column(
                op,
                "mfa_factors",
                sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
                schema="accounts",
            )
        if "is_deleted" not in existing:
            safe_add_column(
                op,
                "mfa_factors",
                sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
                schema="accounts",
            )
        if "updated_at" not in existing:
            safe_add_column(
                op,
                "mfa_factors",
                sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True, server_default=sa.func.now()),
                schema="accounts",
            )
        if "country_code" not in existing:
            safe_add_column(
                op,
                "mfa_factors",
                sa.Column("country_code", sa.String(length=2), nullable=True),
                schema="accounts",
            )
        if "backup_codes" not in existing:
            safe_add_column(
                op,
                "mfa_factors",
                sa.Column("backup_codes", sa.JSON(), nullable=True),
                schema="accounts",
            )
        if "last_used_at" not in existing:
            safe_add_column(
                op,
                "mfa_factors",
                sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
                schema="accounts",
            )
        if "secret" in existing:
            with op.batch_alter_table("mfa_factors", schema="accounts") as batch_op:
                batch_op.alter_column(
                    "secret",
                    existing_type=sa.String(1024),
                    type_=sa.Text(),
                    existing_nullable=True,
                    nullable=True,
                )


def downgrade() -> None:
    bind = op.get_bind()
    if _is_offline(bind):
        return
    if bind.dialect.name == "sqlite":
        return

    if _has_table(bind, "mfa_factors", "accounts"):
        existing = {c["name"] for c in sa.inspect(bind).get_columns("mfa_factors", schema="accounts")}
        if "secret" in existing:
            with op.batch_alter_table("mfa_factors", schema="accounts") as batch_op:
                batch_op.alter_column(
                    "secret",
                    existing_type=sa.Text(),
                    type_=sa.String(1024),
                    existing_nullable=True,
                    nullable=True,
                )
        if "version" in existing:
            op.drop_column("mfa_factors", "version", schema="accounts")
        if "is_deleted" in existing:
            op.drop_column("mfa_factors", "is_deleted", schema="accounts")
        if "updated_at" in existing:
            op.drop_column("mfa_factors", "updated_at", schema="accounts")
        if "country_code" in existing:
            op.drop_column("mfa_factors", "country_code", schema="accounts")
        if "backup_codes" in existing:
            op.drop_column("mfa_factors", "backup_codes", schema="accounts")
        if "last_used_at" in existing:
            op.drop_column("mfa_factors", "last_used_at", schema="accounts")
        op.drop_table("mfa_factors", schema="accounts")
