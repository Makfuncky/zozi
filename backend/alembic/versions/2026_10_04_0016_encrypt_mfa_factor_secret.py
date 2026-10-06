"""alter mfa_factors.secret to support field-encrypted storage

Revision ID: 20261004_0016
Revises: 20261004_0015
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision: str = "20261004_0016_encrypt_mfa_factor_secret"
down_revision: str | None = "20261004_0015_backfill_worm_hash_columns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "mfa_factors",
        "secret",
        existing_type=sa.String(512),
        type_=sa.String(1024),
        schema="accounts",
    )


def downgrade() -> None:
    op.alter_column(
        "mfa_factors",
        "secret",
        existing_type=sa.String(1024),
        type_=sa.String(512),
        schema="accounts",
    )
