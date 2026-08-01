"""add_payment_gateway_connections

Revision ID: e7f8a9b0c1d2
Revises: d6e7f8a9b0c1
Create Date: 2026-04-05 17:05:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = "e7f8a9b0c1d2"
down_revision: Union[str, Sequence[str], None] = "d6e7f8a9b0c1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing = inspector.get_table_names()

    if "payment_gateway_connections" not in existing:
        op.create_table(
            "payment_gateway_connections",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("provider_code", sa.String(length=60), nullable=False),
            sa.Column("provider_kind", sa.String(length=20), nullable=False, server_default="custom"),
            sa.Column("display_name", sa.String(length=120), nullable=False),
            sa.Column("is_enabled", sa.Boolean(), nullable=True, server_default=sa.true()),
            sa.Column("supports_customer_checkout", sa.Boolean(), nullable=True, server_default=sa.false()),
            sa.Column("supports_payouts", sa.Boolean(), nullable=True, server_default=sa.false()),
            sa.Column("mode", sa.String(length=20), nullable=False, server_default="test"),
            sa.Column("public_key", sa.String(length=500), nullable=True),
            sa.Column("secret_key", sa.String(length=1000), nullable=True),
            sa.Column("webhook_secret", sa.String(length=1000), nullable=True),
            sa.Column("merchant_id", sa.String(length=255), nullable=True),
            sa.Column("api_base_url", sa.String(length=500), nullable=True),
            sa.Column("webhook_url", sa.String(length=500), nullable=True),
            sa.Column("test_url", sa.String(length=500), nullable=True),
            sa.Column("supported_currencies_json", sa.Text(), nullable=True),
            sa.Column("extra_config_json", sa.Text(), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("fee_percent", sa.Numeric(8, 4), nullable=False, server_default="0"),
            sa.Column("fixed_fee_amount", sa.Numeric(12, 2), nullable=False, server_default="0"),
            sa.Column("payout_fee_percent", sa.Numeric(8, 4), nullable=False, server_default="0"),
            sa.Column("payout_fixed_fee_amount", sa.Numeric(12, 2), nullable=False, server_default="0"),
            sa.Column("pass_fee_to_customer", sa.Boolean(), nullable=True, server_default=sa.false()),
            sa.Column("test_status", sa.String(length=20), nullable=False, server_default="untested"),
            sa.Column("test_message", sa.String(length=500), nullable=True),
            sa.Column("last_tested_at", sa.DateTime(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.CheckConstraint(
                "provider_kind IN ('stripe', 'tap', 'custom')",
                name="ck_payment_gateway_connections_provider_kind_valid",
            ),
            sa.CheckConstraint(
                "mode IN ('test', 'live')",
                name="ck_payment_gateway_connections_mode_valid",
            ),
            sa.CheckConstraint(
                "test_status IN ('untested', 'passed', 'failed')",
                name="ck_payment_gateway_connections_test_status_valid",
            ),
            sa.CheckConstraint(
                "fee_percent >= 0",
                name="ck_payment_gateway_connections_fee_percent_nonnegative",
            ),
            sa.CheckConstraint(
                "fixed_fee_amount >= 0",
                name="ck_payment_gateway_connections_fixed_fee_nonnegative",
            ),
            sa.CheckConstraint(
                "payout_fee_percent >= 0",
                name="ck_payment_gateway_connections_payout_fee_percent_nonnegative",
            ),
            sa.CheckConstraint(
                "payout_fixed_fee_amount >= 0",
                name="ck_payment_gateway_connections_payout_fixed_fee_nonnegative",
            ),
            sa.ForeignKeyConstraint(["updated_by"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("provider_code", name="uq_payment_gateway_connections_provider_code"),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing = inspector.get_table_names()

    if "payment_gateway_connections" in existing:
        op.drop_table("payment_gateway_connections")

