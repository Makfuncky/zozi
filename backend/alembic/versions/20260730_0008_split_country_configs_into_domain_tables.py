"""split_country_configs_into_domain_tables

Revision ID: 20260730_0008
Revises: 20260730_0007_fix_country_code_width
Create Date: 2026-07-30
"""
from decimal import Decimal
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "20260730_0008"
down_revision: Union[str, None] = "20260730_0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        return

    op.create_table(
        "country_basics",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(3), unique=True, nullable=False, index=True),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("currency", sa.String(3), default="USD"),
        sa.Column("currency_symbol", sa.String(10), nullable=True),
        sa.Column("phone_code", sa.String(10), nullable=True),
        sa.Column("language", sa.String(10), default="en"),
        sa.Column("timezone", sa.String(60), nullable=True),
        sa.Column("date_format", sa.String(20), default="DD/MM/YYYY"),
        sa.Column("status", sa.String(20), default="active"),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("is_deleted", sa.Boolean, default=False),
        sa.Column("is_default", sa.Boolean, default=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("created_by", sa.Integer, nullable=True),
        sa.Column("updated_by", sa.Integer, nullable=True),
        sa.Column("official_name", sa.String(200), nullable=True),
        sa.Column("alpha3", sa.String(3), nullable=True),
        sa.Column("flag_url", sa.String(500), nullable=True),
        sa.Column("currency_name", sa.String(50), nullable=True),
        sa.Column("exchange_rate_to_usd", sa.Numeric(12, 6), nullable=True),
        sa.Column("capital", sa.String(100), nullable=True),
        sa.Column("region", sa.String(60), nullable=True),
        sa.Column("subregion", sa.String(60), nullable=True),
        sa.Column("population", sa.Integer, nullable=True),
        sa.Column("internet_penetration_pct", sa.Numeric(5, 2), nullable=True),
        sa.Column("gdp_per_capita_usd", sa.Numeric(12, 2), nullable=True),
        sa.Column("urbanization_pct", sa.Numeric(5, 2), nullable=True),
        sa.Column("mobile_subs_per_100", sa.Numeric(5, 2), nullable=True),
        sa.Column("public_holidays_json", sa.Text, nullable=True),
        sa.Column("macro_indicators_json", sa.Text, nullable=True),
        schema="country",
    )
    op.create_index("ix_country_basics_code", "country_basics", ["code"], unique=True)

    op.create_table(
        "country_economics",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("country_code", sa.String(3), sa.ForeignKey("country.country_configs.code"), nullable=False, unique=True),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("is_deleted", sa.Boolean, default=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("created_by", sa.Integer, nullable=True),
        sa.Column("updated_by", sa.Integer, nullable=True),
        sa.Column("economic_tier", sa.String(20), nullable=True),
        sa.Column("fraud_risk_tier", sa.String(10), nullable=True),
        sa.Column("suggested_logistics_model", sa.String(30), nullable=True),
        sa.Column("data_residency_tier", sa.String(20), default="standard"),
        sa.Column("data_residency_encrypted", sa.Text, nullable=True),
        sa.Column("confidence_score", sa.Numeric(5, 4), default=Decimal("0.0000")),
        sa.Column("audit_trail_json", sa.Text, nullable=True),
        sa.Column("cod_enabled", sa.String(1), nullable=True),
        sa.Column("cod_max_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("cod_verification_required", sa.String(1), nullable=True),
        sa.Column("cod_remittance_days", sa.Integer, nullable=True),
        sa.Column("settlement_hold_days", sa.Integer, default=3),
        sa.Column("minimum_payout_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("payout_currency", sa.String(10), nullable=True),
        sa.Column("supplier_kyc_tier", sa.String(20), nullable=True),
        sa.Column("supplier_onboarding_fee", sa.Numeric(12, 2), nullable=True),
        sa.Column("supplier_monthly_fee", sa.Numeric(12, 2), nullable=True),
        sa.Column("supplier_rating_threshold", sa.Numeric(5, 2), nullable=True),
        sa.Column("legal_entity_required", sa.String(1), default="false"),
        sa.Column("consumer_protection_days", sa.Integer, default=14),
        sa.Column("data_privacy_framework", sa.String(20), nullable=True),
        sa.Column("max_package_weight_kg", sa.Numeric(8, 2), nullable=True),
        sa.Column("max_package_dimensions_cm", sa.String(200), nullable=True),
        sa.Column("signature_required_threshold", sa.Numeric(10, 2), nullable=True),
        sa.Column("measurement_system", sa.String(10), default="metric"),
        sa.Column("working_days_json", sa.Text, default="[]"),
        sa.Column("supported_languages_json", sa.Text, default="[]"),
        sa.Column("payout_methods_json", sa.Text, default="[]"),
        sa.Column("logistics_zones_json", sa.Text, default="[]"),
        schema="country",
    )
    op.create_index("ix_country_economics_code", "country_economics", ["country_code"], unique=True)

    op.create_table(
        "country_tax",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("country_code", sa.String(3), sa.ForeignKey("country.country_configs.code"), nullable=False, unique=True),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("is_deleted", sa.Boolean, default=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("created_by", sa.Integer, nullable=True),
        sa.Column("updated_by", sa.Integer, nullable=True),
        sa.Column("tax_type", sa.String(20), default="VAT"),
        sa.Column("tax_rate", sa.Numeric(5, 4), default=Decimal("0.0000")),
        sa.Column("tax_name", sa.String(50), default="VAT"),
        sa.Column("tax_inclusive", sa.Boolean, default=False),
        sa.Column("tax_exempt_categories_json", sa.Text, default="[]"),
        sa.Column("tax_reduced_rates_json", sa.Text, default="{}"),
        schema="country",
    )
    op.create_index("ix_country_tax_code", "country_tax", ["country_code"], unique=True)

    op.create_table(
        "country_legal",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("country_code", sa.String(3), sa.ForeignKey("country.country_configs.code"), nullable=False, unique=True),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("is_deleted", sa.Boolean, default=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("created_by", sa.Integer, nullable=True),
        sa.Column("updated_by", sa.Integer, nullable=True),
        sa.Column("legal_entity_required", sa.String(1), default="true"),
        sa.Column("consumer_protection_days", sa.Integer, default=14),
        sa.Column("data_privacy_framework", sa.String(20), nullable=True),
        sa.Column("gdpr_compliant", sa.Boolean, default=False),
        sa.Column("local_data_residency", sa.Boolean, default=False),
        sa.Column("compliance_score", sa.Numeric(5, 4), default=Decimal("0.5000")),
        sa.Column("legal_risk_tier", sa.String(10), default="medium"),
        sa.Column("contract_templates_json", sa.Text, default="[]"),
        sa.Column("regulatory_bodies_json", sa.Text, default="[]"),
        schema="country",
    )
    op.create_index("ix_country_legal_code", "country_legal", ["country_code"], unique=True)

    with op.batch_alter_table("country_configs") as batch_op:
        batch_op.add_column("basics_id", sa.Integer(sa.ForeignKey("country.country_basics.id"), nullable=True))
        batch_op.add_column("economics_id", sa.Integer(sa.ForeignKey("country.country_economics.id"), nullable=True))
        batch_op.add_column("tax_id", sa.Integer(sa.ForeignKey("country.country_tax.id"), nullable=True))
        batch_op.add_column("legal_id", sa.Integer(sa.ForeignKey("country.country_legal.id"), nullable=True))


def downgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        return

    with op.batch_alter_table("country_configs") as batch_op:
        batch_op.drop_column("legal_id")
        batch_op.drop_column("tax_id")
        batch_op.drop_column("economics_id")
        batch_op.drop_column("basics_id")

    op.drop_table("country_legal")
    op.drop_table("country_tax")
    op.drop_table("country_economics")
    op.drop_table("country_basics")