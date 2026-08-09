"""add_email_provider_runtime_config

Revision ID: y4z5a6b7c8d9
Revises: v3w4x5y6z7a8
Create Date: 2026-04-04 00:20:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = "y4z5a6b7c8d9"
down_revision: Union[str, Sequence[str], None] = "v3w4x5y6z7a8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing = inspector.get_table_names()

    if "email_provider_configs" not in existing:
        op.create_table(
            "email_provider_configs",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("provider", sa.String(length=30), nullable=False, server_default="environment"),
            sa.Column("resend_api_key", sa.String(length=500), nullable=True),
            sa.Column("resend_webhook_secret", sa.String(length=500), nullable=True),
            sa.Column("smtp_host", sa.String(length=255), nullable=True),
            sa.Column("smtp_port", sa.Integer(), nullable=False, server_default="587"),
            sa.Column("smtp_username", sa.String(length=255), nullable=True),
            sa.Column("smtp_password", sa.String(length=500), nullable=True),
            sa.Column("smtp_use_tls", sa.Boolean(), nullable=True, server_default=sa.true()),
            sa.Column("smtp_use_ssl", sa.Boolean(), nullable=True, server_default=sa.false()),
            sa.Column("smtp_timeout_seconds", sa.Integer(), nullable=False, server_default="15"),
            sa.Column("email_from_default", sa.String(length=255), nullable=True),
            sa.Column("email_from_promotional", sa.String(length=255), nullable=True),
            sa.Column("email_from_transactional", sa.String(length=255), nullable=True),
            sa.Column("email_from_notification", sa.String(length=255), nullable=True),
            sa.Column("email_from_alert", sa.String(length=255), nullable=True),
            sa.Column("email_from_verification", sa.String(length=255), nullable=True),
            sa.Column("email_from_login_verification", sa.String(length=255), nullable=True),
            sa.Column("email_from_password_reset", sa.String(length=255), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.CheckConstraint(
                "provider IN ('environment', 'resend', 'smtp', 'disabled')",
                name="ck_email_provider_configs_provider_valid",
            ),
            sa.ForeignKeyConstraint(["updated_by"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing = inspector.get_table_names()

    if "email_provider_configs" in existing:
        op.drop_table("email_provider_configs")

