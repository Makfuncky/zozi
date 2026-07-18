"""add_email_provider_config

Revision ID: d6e7f8a9b0c2
Revises: d6e7f8a9b0c1
Create Date: 2026-04-05 10:35:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = "d6e7f8a9b0c2"
down_revision: Union[str, Sequence[str], None] = "d6e7f8a9b0c1"
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
            sa.Column("provider", sa.String(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=True, server_default="true"),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.Column("email_from_default", sa.String(), nullable=True),
            sa.Column("email_from_promotional", sa.String(), nullable=True),
            sa.Column("email_from_transactional", sa.String(), nullable=True),
            sa.Column("email_from_notification", sa.String(), nullable=True),
            sa.Column("email_from_alert", sa.String(), nullable=True),
            sa.Column("email_from_verification", sa.String(), nullable=True),
            sa.Column("email_from_login_verification", sa.String(), nullable=True),
            sa.Column("email_from_password_reset", sa.String(), nullable=True),
            sa.Column("resend_api_key", sa.String(), nullable=True),
            sa.Column("resend_webhook_secret", sa.String(), nullable=True),
            sa.Column("smtp_host", sa.String(), nullable=True),
            sa.Column("smtp_port", sa.Integer(), nullable=True),
            sa.Column("smtp_username", sa.String(), nullable=True),
            sa.Column("smtp_password", sa.String(), nullable=True),
            sa.Column("smtp_use_tls", sa.Boolean(), nullable=True, server_default="true"),
            sa.Column("smtp_use_ssl", sa.Boolean(), nullable=True, server_default="false"),
            sa.Column("smtp_timeout_seconds", sa.Integer(), nullable=True, server_default="10"),
            sa.ForeignKeyConstraint(["updated_by"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing = inspector.get_table_names()

    if "email_provider_configs" in existing:
        op.drop_table("email_provider_configs")
