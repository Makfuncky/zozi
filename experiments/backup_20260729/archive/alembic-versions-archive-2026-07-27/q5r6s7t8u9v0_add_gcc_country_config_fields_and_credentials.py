"""add_gcc_country_config_fields_and_credentials

Adds missing GCC extended country configuration columns and creates the
country_gateway_credentials table for encrypted per-country gateway credentials.

Revision ID: q5r6s7t8u9v0
Revises: d5477adebb01
Create Date: 2026-06-22 10:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "q5r6s7t8u9v0"
down_revision: Union[str, Sequence[str], None] = "d5477adebb01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("country_configs"):
        return
    country_configs_table = inspector.get_columns("country_configs")
    existing_cols = {col["name"] for col in country_configs_table}

    GCC_COLUMNS = {
        "currency_symbol": sa.String(10),
        "phone_code": sa.String(10),
        "language": sa.String(10),
        "payment_gateways_json": sa.Text(),
        "logistics_providers_json": sa.Text(),
        "legal_rules_json": sa.Text(),
        "regions_json": sa.Text(),
        "supplier_requirements_json": sa.Text(),
        "payout_settings_json": sa.Text(),
        "commission_tiers_json": sa.Text(),
        "date_format": sa.String(20),
        "address_format_json": sa.Text(),
        "product_restrictions_json": sa.Text(),
    }

    with op.batch_alter_table("country_configs") as batch_op:
        for col_name, col_type in GCC_COLUMNS.items():
            if col_name not in existing_cols:
                batch_op.add_column(sa.Column(col_name, col_type, nullable=True))
        if "language" not in existing_cols:
            batch_op.alter_column("language", server_default="en")

    if not inspector.has_table("country_gateway_credentials"):
        op.create_table(
            "country_gateway_credentials",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("country_code", sa.String(10), nullable=False),
            sa.Column("gateway_id", sa.String(60), nullable=False),
            sa.Column("environment", sa.String(20), nullable=False, server_default="test"),
            sa.Column("encrypted_credentials", sa.Text(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
            sa.Column("last_rotated_at", sa.DateTime(), nullable=True),
            sa.Column("rotated_by", sa.Integer(), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["country_code"], ["country_configs.code"]),
            sa.ForeignKeyConstraint(["rotated_by"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "country_code", "gateway_id", "environment",
                name="uq_country_gateway_creds_triplet",
            ),
        )
        op.create_index(
            "ix_country_gateway_credentials_country",
            "country_gateway_credentials",
            ["country_code", "gateway_id"],
        )
        op.create_index(
            "ix_country_gateway_credentials_id",
            "country_gateway_credentials",
            ["id"],
        )


def downgrade() -> None:
    if op.get_bind().dialect.has_table(op.get_bind(), "country_gateway_credentials"):
        bind = op.get_bind()
        inspector = sa.inspect(bind)
        if not inspector.has_table("country_configs"):
            return
        op.drop_index("ix_country_gateway_credentials_country", table_name="country_gateway_credentials")
        op.drop_index("ix_country_gateway_credentials_id", table_name="country_gateway_credentials")
        op.drop_table("country_gateway_credentials")

    with op.batch_alter_table("country_configs") as batch_op:
        batch_op.drop_column("product_restrictions_json")
        batch_op.drop_column("address_format_json")
        batch_op.drop_column("date_format")
        batch_op.drop_column("commission_tiers_json")
        batch_op.drop_column("payout_settings_json")
        batch_op.drop_column("supplier_requirements_json")
        batch_op.drop_column("regions_json")
        batch_op.drop_column("legal_rules_json")
        batch_op.drop_column("logistics_providers_json")
        batch_op.drop_column("payment_gateways_json")
        batch_op.drop_column("language")
        batch_op.drop_column("phone_code")
        batch_op.drop_column("currency_symbol")

