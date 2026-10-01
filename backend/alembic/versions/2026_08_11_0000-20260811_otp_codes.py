"""create otp_codes table (OTP/MFA challenge store)

Backs the per-actor OTP/MFA auth surface (``modules.admin.auth.otp``). The table
lives in the ``core`` schema alongside ``users``. On PostgreSQL it is created by
this migration; in dev (SQLite) the table is produced by ``create_all``, matching
the project's existing dev(create_all)/prod(alembic) split.

Revision ID: 20260811_otp_codes
Revises: 20260810_emp_act_log
Create Date: 2026-08-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260811_otp_codes"
down_revision: Union[str, None] = "20260810_emp_act_log"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLE = "otp_codes"
_SCHEMA = "core"


def upgrade() -> None:
    if op.get_context().dialect.name != "postgresql":
        return

    op.execute("CREATE SCHEMA IF NOT EXISTS core")

    op.create_table(
        _TABLE,
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("core.users.id"), nullable=False),
        sa.Column("purpose", sa.String(32), nullable=False),
        sa.Column("channel", sa.String(16), nullable=False, server_default="email"),
        sa.Column("destination", sa.String(320), nullable=True),
        sa.Column("code_hash", sa.String, nullable=False),
        sa.Column("expires_at", sa.DateTime, nullable=False),
        sa.Column("attempts", sa.Integer, nullable=False, server_default="0"),
        sa.Column("verified", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("country_code", sa.String(10), sa.ForeignKey("country.country_configs.code"), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=True),
        schema=_SCHEMA,
    )
    op.create_index("ix_otp_codes_user_purpose", _TABLE, ["user_id", "purpose"], schema=_SCHEMA)


def downgrade() -> None:
    if op.get_context().dialect.name != "postgresql":
        return

    op.drop_index("ix_otp_codes_user_purpose", table_name=_TABLE, schema=_SCHEMA)
    op.drop_table(_TABLE, schema=_SCHEMA)
