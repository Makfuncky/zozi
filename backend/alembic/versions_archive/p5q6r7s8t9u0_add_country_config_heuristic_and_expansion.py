"""add_country_config_heuristic_and_expansion

Phase 1: Database schema expansion for country management system.

Adds heuristic persistence columns, expanded identity fields, COD settings,
logistics defaults, CountryCity expansion columns, and indexes.

Revision ID: p5q6r7s8t9u0
Revises: m0n1o2p3q4r5
Create Date: 2026-06-24 14:00:00.000000

"""
from __future__ import annotations

from decimal import Decimal
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "p5q6r7s8t9u0"
down_revision: Union[str, Sequence[str], None] = "m0n1o2p3q4r5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(table: str, column: str) -> bool:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    cols = {c["name"] for c in inspector.get_columns(table)}
    return column in cols


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # ── country_configs: Heuristic persistence columns ─────────────────────
    if not _has_column("country_configs", "economic_tier"):
        op.add_column("country_configs",
            sa.Column("economic_tier", sa.String(20), nullable=True,
                      comment="auto-classified: emerging/developing/developed"))

    if not _has_column("country_configs", "fraud_risk_tier"):
        op.add_column("country_configs",
            sa.Column("fraud_risk_tier", sa.String(10), nullable=True,
                      comment="auto-assigned: low/medium/high"))

    if not _has_column("country_configs", "suggested_logistics_model"):
        op.add_column("country_configs",
            sa.Column("suggested_logistics_model", sa.String(30), nullable=True,
                      comment="recommended model: hub_and_spoke/point_to_point/hybrid"))

    if not _has_column("country_configs", "suggested_commission_ranges_json"):
        op.add_column("country_configs",
            sa.Column("suggested_commission_ranges_json", sa.Text, nullable=True,
                      comment="category slug -> min/max/suggested pct"))

    if not _has_column("country_configs", "suggested_gateway_rankings_json"):
        op.add_column("country_configs",
            sa.Column("suggested_gateway_rankings_json", sa.Text, nullable=True,
                      comment="ranked gateway list with feasibility scores"))

    if not _has_column("country_configs", "consumer_behavior_profile_json"):
        op.add_column("country_configs",
            sa.Column("consumer_behavior_profile_json", sa.Text, nullable=True,
                      comment="shopping behavior profile for the country"))

    # ── country_configs: Identity expansion ────────────────────────────────
    if not _has_column("country_configs", "official_name"):
        op.add_column("country_configs",
            sa.Column("official_name", sa.String(200), nullable=True))

    if not _has_column("country_configs", "alpha3"):
        op.add_column("country_configs",
            sa.Column("alpha3", sa.String(3), nullable=True))

    if not _has_column("country_configs", "flag_url"):
        op.add_column("country_configs",
            sa.Column("flag_url", sa.String(500), nullable=True))

    if not _has_column("country_configs", "currency_name"):
        op.add_column("country_configs",
            sa.Column("currency_name", sa.String(60), nullable=True))

    if not _has_column("country_configs", "exchange_rate_to_usd"):
        op.add_column("country_configs",
            sa.Column("exchange_rate_to_usd", sa.Numeric(12, 6), nullable=True))

    # ── country_configs: COD / settlement ──────────────────────────────────
    if not _has_column("country_configs", "cod_enabled"):
        op.add_column("country_configs",
            sa.Column("cod_enabled", sa.Boolean, nullable=True, default=True,
                      comment="cash on delivery available"))

    if not _has_column("country_configs", "cod_max_amount"):
        op.add_column("country_configs",
            sa.Column("cod_max_amount", sa.Numeric(12, 2), nullable=True))

    if not _has_column("country_configs", "cod_verification_required"):
        op.add_column("country_configs",
            sa.Column("cod_verification_required", sa.Boolean, nullable=True, default=False))

    if not _has_column("country_configs", "cod_remittance_days"):
        op.add_column("country_configs",
            sa.Column("cod_remittance_days", sa.Integer, nullable=True, default=7))

    if not _has_column("country_configs", "settlement_hold_days"):
        op.add_column("country_configs",
            sa.Column("settlement_hold_days", sa.Integer, nullable=True, default=3))

    if not _has_column("country_configs", "minimum_payout_amount"):
        op.add_column("country_configs",
            sa.Column("minimum_payout_amount", sa.Numeric(12, 2), nullable=True))

    if not _has_column("country_configs", "payout_currency"):
        op.add_column("country_configs",
            sa.Column("payout_currency", sa.String(10), nullable=True))

    # ── country_configs: Supplier defaults ─────────────────────────────────
    if not _has_column("country_configs", "supplier_kyc_tier"):
        op.add_column("country_configs",
            sa.Column("supplier_kyc_tier", sa.String(10), nullable=True,
                      comment="auto-assigned: basic/standard/strict"))

    if not _has_column("country_configs", "supplier_onboarding_fee"):
        op.add_column("country_configs",
            sa.Column("supplier_onboarding_fee", sa.Numeric(12, 2), nullable=True, default=0))

    if not _has_column("country_configs", "supplier_monthly_fee"):
        op.add_column("country_configs",
            sa.Column("supplier_monthly_fee", sa.Numeric(12, 2), nullable=True, default=0))

    if not _has_column("country_configs", "supplier_rating_threshold"):
        op.add_column("country_configs",
            sa.Column("supplier_rating_threshold", sa.Numeric(3, 2), nullable=True, default=Decimal("0.00")))

    # ── country_configs: Legal / consumer protection ───────────────────────
    if not _has_column("country_configs", "legal_entity_required"):
        op.add_column("country_configs",
            sa.Column("legal_entity_required", sa.Boolean, nullable=True, default=False))

    if not _has_column("country_configs", "consumer_protection_days"):
        op.add_column("country_configs",
            sa.Column("consumer_protection_days", sa.Integer, nullable=True, default=14))

    if not _has_column("country_configs", "data_privacy_framework"):
        op.add_column("country_configs",
            sa.Column("data_privacy_framework", sa.String(10), nullable=True, default="None"))

    # ── country_configs: Logistics expansion ───────────────────────────────
    if not _has_column("country_configs", "max_package_weight_kg"):
        op.add_column("country_configs",
            sa.Column("max_package_weight_kg", sa.Numeric(8, 2), nullable=True))

    if not _has_column("country_configs", "max_package_dimensions_cm"):
        op.add_column("country_configs",
            sa.Column("max_package_dimensions_cm", sa.String(200), nullable=True,
                      comment="JSON array [L,W,H] in cm"))

    if not _has_column("country_configs", "signature_required_threshold"):
        op.add_column("country_configs",
            sa.Column("signature_required_threshold", sa.Numeric(12, 2), nullable=True))

    # ── country_configs: Locale ────────────────────────────────────────────
    if not _has_column("country_configs", "measurement_system"):
        op.add_column("country_configs",
            sa.Column("measurement_system", sa.String(10), nullable=True, default="metric",
                      comment="metric/imperial"))

    if not _has_column("country_configs", "working_days_json"):
        op.add_column("country_configs",
            sa.Column("working_days_json", sa.Text, nullable=True,
                      comment='JSON array, e.g. ["sun","mon","tue","wed","thu"]'))

    # ── country_cities: Expansion columns ──────────────────────────────────
    if not _has_column("country_cities", "name_local"):
        op.add_column("country_cities",
            sa.Column("name_local", sa.String(200), nullable=True,
                      comment="City name in local language/script"))

    if not _has_column("country_cities", "is_capital"):
        op.add_column("country_cities",
            sa.Column("is_capital", sa.Boolean, nullable=True, default=False))

    if not _has_column("country_cities", "postal_code_prefix"):
        op.add_column("country_cities",
            sa.Column("postal_code_prefix", sa.String(10), nullable=True))

    if not _has_column("country_cities", "logistics_zone_id"):
        op.add_column("country_cities",
            sa.Column("logistics_zone_id", sa.String(60), nullable=True,
                      comment="FK-like reference to logistics zone"))

    # ── Indexes ────────────────────────────────────────────────────────────
    inspector = sa.inspect(bind)
    existing_indexes = {ix["name"] for ix in inspector.get_indexes("country_cities")}
    if "ix_country_cities_country_population" not in existing_indexes:
        op.create_index("ix_country_cities_country_population", "country_cities",
                        ["country_code", sa.text("population DESC")])
    if "ix_country_cities_country_active" not in existing_indexes:
        op.create_index("ix_country_cities_country_active", "country_cities",
                        ["country_code"])

    existing_cc_indexes = {ix["name"] for ix in inspector.get_indexes("country_configs")}
    if "ix_country_configs_economic_tier" not in existing_cc_indexes:
        op.create_index("ix_country_configs_economic_tier", "country_configs", ["economic_tier"])
    if "ix_country_configs_fraud_tier" not in existing_cc_indexes:
        op.create_index("ix_country_configs_fraud_tier", "country_configs", ["fraud_risk_tier"])


def downgrade() -> None:
    # country_configs heuristic columns
    for col in (
        "economic_tier", "fraud_risk_tier", "suggested_logistics_model",
        "suggested_commission_ranges_json", "suggested_gateway_rankings_json",
        "consumer_behavior_profile_json",
    ):
        if _has_column("country_configs", col):
            op.drop_column("country_configs", col)

    # country_configs identity
    for col in ("official_name", "alpha3", "flag_url", "currency_name", "exchange_rate_to_usd"):
        if _has_column("country_configs", col):
            op.drop_column("country_configs", col)

    # country_configs COD
    for col in ("cod_enabled", "cod_max_amount", "cod_verification_required",
                "cod_remittance_days", "settlement_hold_days", "minimum_payout_amount",
                "payout_currency"):
        if _has_column("country_configs", col):
            op.drop_column("country_configs", col)

    # country_configs supplier
    for col in ("supplier_kyc_tier", "supplier_onboarding_fee", "supplier_monthly_fee",
                "supplier_rating_threshold"):
        if _has_column("country_configs", col):
            op.drop_column("country_configs", col)

    # country_configs legal
    for col in ("legal_entity_required", "consumer_protection_days", "data_privacy_framework"):
        if _has_column("country_configs", col):
            op.drop_column("country_configs", col)

    # country_configs logistics
    for col in ("max_package_weight_kg", "max_package_dimensions_cm", "signature_required_threshold"):
        if _has_column("country_configs", col):
            op.drop_column("country_configs", col)

    # country_configs locale
    for col in ("measurement_system", "working_days_json"):
        if _has_column("country_configs", col):
            op.drop_column("country_configs", col)

    # country_cities
    for col in ("name_local", "is_capital", "postal_code_prefix", "logistics_zone_id"):
        if _has_column("country_cities", col):
            op.drop_column("country_cities", col)

    # Indexes
    for idx in ("ix_country_cities_country_population", "ix_country_cities_country_active",
                "ix_country_configs_economic_tier", "ix_country_configs_fraud_tier"):
        try:
            op.drop_index(idx)
        except Exception:
            pass

