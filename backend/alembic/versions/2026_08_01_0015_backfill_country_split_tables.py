"""backfill_country_split_tables

Data migration that populates ``country_basics``, ``country_economics``,
``country_tax``, and ``country_legal`` from the legacy ``country_configs``
table, and wires the ``basics_id`` / ``economics_id`` / ``tax_id`` /
``legal_id`` FK columns on ``country_configs`` (Constitution §4 Phase 5,
§8.3 expand-then-migrate-then-contract).

The legacy columns on ``country_configs`` are kept (contraction is a
separate, later release) so the migration is reversible and rollback-safe.

Revision ID: 20260801_0015
Revises: 20260801_0014
Create Date: 2026-08-01
"""
import os
import sys
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(_project_root, "alembic"))
sys.path.insert(0, _project_root)

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260801_0015"
down_revision: Union[str, None] = "20260801_0014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        return

    op.execute("CREATE SCHEMA IF NOT EXISTS country")

    op.execute(
        """
        INSERT INTO country.country_basics (
            code, name, currency, currency_symbol, phone_code, language,
            timezone, date_format, status, is_active, is_deleted, is_default,
            created_at, updated_at, created_by, updated_by,
            official_name, alpha3, flag_url, currency_name, exchange_rate_to_usd,
            capital, region, subregion, population,
            internet_penetration_pct, gdp_per_capita_usd,
            urbanization_pct, mobile_subs_per_100,
            public_holidays_json, macro_indicators_json
        )
        SELECT
            code, name, currency, currency_symbol, phone_code, language,
            timezone, date_format, status, is_active, is_deleted, is_default,
            created_at, updated_at, created_by, updated_by,
            official_name, alpha3, flag_url, currency_name, exchange_rate_to_usd,
            capital, region, subregion, population,
            internet_penetration_pct, gdp_per_capita_usd,
            urbanization_pct, mobile_subs_per_100,
            public_holidays_json, macro_indicators_json
        FROM country.country_configs
        ON CONFLICT (code) DO NOTHING
        """
    )

    op.execute(
        """
        INSERT INTO country.country_economics (
            country_code, is_active, is_deleted, created_at, updated_at,
            created_by, updated_by,
            economic_tier, fraud_risk_tier, suggested_logistics_model,
            data_residency_tier, data_residency_encrypted, confidence_score,
            audit_trail_json, cod_enabled, cod_max_amount,
            cod_verification_required, cod_remittance_days, settlement_hold_days,
            minimum_payout_amount, payout_currency,
            supplier_kyc_tier, supplier_onboarding_fee, supplier_monthly_fee,
            supplier_rating_threshold, legal_entity_required,
            consumer_protection_days, data_privacy_framework,
            max_package_weight_kg, max_package_dimensions_cm,
            signature_required_threshold, measurement_system,
            working_days_json, supported_languages_json, payout_methods_json,
            logistics_zones_json
        )
        SELECT
            code, is_active, is_deleted, created_at, updated_at,
            created_by, updated_by,
            economic_tier, fraud_risk_tier, suggested_logistics_model,
            data_residency_tier, data_residency_encrypted, confidence_score,
            audit_trail_json, cod_enabled, cod_max_amount,
            cod_verification_required, cod_remittance_days, settlement_hold_days,
            minimum_payout_amount, payout_currency,
            supplier_kyc_tier, supplier_onboarding_fee, supplier_monthly_fee,
            supplier_rating_threshold, legal_entity_required,
            consumer_protection_days, data_privacy_framework,
            max_package_weight_kg, max_package_dimensions_cm,
            signature_required_threshold, measurement_system,
            working_days_json, supported_languages_json, payout_methods_json,
            logistics_zones_json
        FROM country.country_configs
        ON CONFLICT (country_code) DO NOTHING
        """
    )

    op.execute(
        """
        INSERT INTO country.country_tax (
            country_code, is_active, is_deleted, created_at, updated_at,
            created_by, updated_by,
            tax_type, tax_rate, tax_name, tax_inclusive,
            tax_exempt_categories_json, tax_reduced_rates_json
        )
        SELECT
            code, is_active, is_deleted, created_at, updated_at,
            created_by, updated_by,
            tax_type, tax_rate, tax_name, tax_inclusive,
            tax_exempt_categories_json, tax_reduced_rates_json
        FROM country.country_configs
        ON CONFLICT (country_code) DO NOTHING
        """
    )

    op.execute(
        """
        INSERT INTO country.country_legal (
            country_code, is_active, is_deleted, created_at, updated_at,
            created_by, updated_by,
            legal_entity_required, consumer_protection_days, data_privacy_framework,
            gdpr_compliant, local_data_residency, compliance_score,
            legal_risk_tier, contract_templates_json, regulatory_bodies_json
        )
        SELECT
            code, is_active, is_deleted, created_at, updated_at,
            created_by, updated_by,
            legal_entity_required, consumer_protection_days, data_privacy_framework,
            false, false, COALESCE(confidence_score, 0.5000),
            'medium', '[]', '[]'
        FROM country.country_configs
        ON CONFLICT (country_code) DO NOTHING
        """
    )

    op.execute(
        """
        UPDATE country.country_configs AS cc
        SET basics_id = cb.id
        FROM country.country_basics AS cb
        WHERE cc.code = cb.code
          AND cc.basics_id IS NULL
        """
    )
    op.execute(
        """
        UPDATE country.country_configs AS cc
        SET economics_id = ce.id
        FROM country.country_economics AS ce
        WHERE cc.code = ce.country_code
          AND cc.economics_id IS NULL
        """
    )
    op.execute(
        """
        UPDATE country.country_configs AS cc
        SET tax_id = ct.id
        FROM country.country_tax AS ct
        WHERE cc.code = ct.country_code
          AND cc.tax_id IS NULL
        """
    )
    op.execute(
        """
        UPDATE country.country_configs AS cc
        SET legal_id = cl.id
        FROM country.country_legal AS cl
        WHERE cc.code = cl.country_code
          AND cc.legal_id IS NULL
        """
    )


def downgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        return

    op.execute("TRUNCATE TABLE country.country_basics RESTART IDENTITY CASCADE")
    op.execute("TRUNCATE TABLE country.country_economics RESTART IDENTITY CASCADE")
    op.execute("TRUNCATE TABLE country.country_tax RESTART IDENTITY CASCADE")
    op.execute("TRUNCATE TABLE country.country_legal RESTART IDENTITY CASCADE")

    op.execute("UPDATE country.country_configs SET basics_id = NULL")
    op.execute("UPDATE country.country_configs SET economics_id = NULL")
    op.execute("UPDATE country.country_configs SET tax_id = NULL")
    op.execute("UPDATE country.country_configs SET legal_id = NULL")
