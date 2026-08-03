"""Tests for country_research.py — 20-module report builder."""

import json
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from data.services_country_research import build_country_research, DEFAULT_MODULES


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_auto_data():
    return {
        "code": "IN",
        "name": "India",
        "official_name": "Republic of India",
        "alpha3": "IND",
        "numeric_code": "356",
        "capital": "New Delhi",
        "flag_url": "https://flagcdn.com/in.svg",
        "region": "Asia",
        "subregion": "Southern Asia",
        "area_km2": 3287263,
        "population": 1400000000,
        "timezone": "UTC+05:30",
        "language": "hi",
        "languages": ["Hindi", "English"],
        "currencies": ["INR"],
        "currency": "INR",
        "currency_symbol": "\u20b9",
        "currency_name": "Indian Rupee",
        "phone_code": "+91",
        "latitude": 20.0,
        "longitude": 77.0,
        "google_maps": "https://maps.google.com/?q=India",
        "internet_penetration_pct": 52.0,
        "gdp_per_capita_usd": 2400.0,
        "gdp_usd": 3940000000000.0,
        "gdp_per_capita_ppp_usd": 9183.0,
        "gdp_growth_pct": 6.5,
        "inflation_pct": 5.1,
        "unemployment_pct": 7.2,
        "gini_index": 35.7,
        "government_debt_pct_gdp": 70.0,
        "current_account_balance_pct_gdp": -1.2,
        "literacy_rate_pct": 77.7,
        "urban_population_pct": 35.0,
        "economic_tier": "emerging",
        "tax_type": "GST",
        "tax_rate": 0.18,
        "tax_name": "Goods and Services Tax",
        "confidence_score": 0.85,
        "fraud_risk_tier": "medium",
        "logistics_model": "point_to_point",
        "data_privacy_framework": "PDPL",
        "data_residency_tier": "standard",
        "legal_rules": {
            "minimum_order_age": 18,
            "max_returns_allowed": 3,
            "return_window_days": 14,
            "refund_processing_days": 7,
            "requires_commercial_license": True,
            "requires_vat_registration": True,
            "product_restrictions": [],
        },
        "payment_gateways": [
            {
                "gateway_id": "stripe",
                "name": "Stripe",
                "type": "card",
                "fee_percentage": 2.9,
            },
            {
                "gateway_id": "razorpay",
                "name": "Razorpay",
                "type": "card",
                "fee_percentage": 2.0,
            },
        ],
        "public_holidays": [
            {"name": "Republic Day", "date": "2026-01-26", "local_name": "Republic Day"},
            {"name": "Independence Day", "date": "2026-08-15", "local_name": "Independence Day"},
        ],
        "cities": [
            {"name": "Mumbai", "population": 12480000, "is_capital": False},
            {"name": "Delhi", "population": 11000000, "is_capital": True},
        ],
        "fetched_at": "2026-07-25T12:00:00Z",
        "cached": False,
    }


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestBuildCountryResearch:
    def test_returns_all_20_modules(self, sample_auto_data):
        result = build_country_research(sample_auto_data)
        module_keys = [k for k in result if k.startswith("module_")]
        assert len(module_keys) == 20

    def test_meta_present(self, sample_auto_data):
        result = build_country_research(sample_auto_data)
        assert "meta" in result
        meta = result["meta"]
        assert meta["country_code"] == "IN"
        assert meta["country_name"] == "India"
        assert meta["overall_confidence"] in ("high", "medium", "low")
        assert meta["modules_total"] == 20
        assert "generated_at_utc" in meta

    def test_module_01_identity_keys(self, sample_auto_data):
        result = build_country_research(sample_auto_data)
        m1 = result["module_01_country_identity"]
        assert m1["official_name"] == "Republic of India"
        assert m1["common_name"] == "India"
        assert m1["country_code_alpha2"] == "IN"
        assert m1["country_code_alpha3"] == "IND"
        assert m1["numeric_code"] == "356"
        assert m1["capital"] == "New Delhi"
        assert m1["currency_code"] == "INR"
        assert m1["currency_symbol"] == "\u20b9"
        assert m1["area_km2"] == 3287263
        assert m1["google_maps"] == "https://maps.google.com/?q=India"
        assert m1["latitude"] == 20.0
        assert m1["longitude"] == 77.0

    def test_module_02_demographics_keys(self, sample_auto_data):
        result = build_country_research(sample_auto_data)
        m2 = result["module_02_demographics"]
        assert m2["total_population"] == 1400000000
        assert m2["internet_penetration_pct"] == 52.0
        assert m2["economic_tier"] == "emerging"
        assert m2["urban_population_pct"] == 35.0
        assert m2["literacy_rate_pct"] == 77.7
        assert len(m2["top_cities"]) == 2

    def test_module_03_economy_keys(self, sample_auto_data):
        result = build_country_research(sample_auto_data)
        m3 = result["module_03_economy_wealth"]
        assert m3["gdp_per_capita_usd"] == 2400.0
        assert m3["tax_rate"] == 0.18
        assert m3["tax_type"] == "GST"
        assert m3["gdp_usd"] == 3940000000000.0
        assert m3["gdp_growth_pct"] == 6.5
        assert m3["inflation_pct"] == 5.1
        assert m3["unemployment_pct"] == 7.2
        assert m3["gini_index"] == 35.7
        assert m3["urban_population_pct"] == 35.0
        assert m3["literacy_rate_pct"] == 77.7

    def test_holidays_populate_seasonality(self, sample_auto_data):
        result = build_country_research(sample_auto_data)
        m7 = result["module_07_shopping_seasonality"]
        assert len(m7["major_shopping_festivals"]) == 2
        assert m7["confidence"] == "medium"

    def test_payment_gateways_populate_infrastructure(self, sample_auto_data):
        result = build_country_research(sample_auto_data)
        m9 = result["module_09_payment_infrastructure"]
        assert len(m9["top_5_payment_gateways"]) == 2
        assert m9["confidence"] == "medium"

    def test_legal_rules_populate_regulations(self, sample_auto_data):
        result = build_country_research(sample_auto_data)
        m11 = result["module_11_legal_regulations"]
        assert "14" in m11["mandatory_return_refund_window"]
        assert m11["confidence"] == "medium"

    def test_default_modules_have_low_confidence(self, sample_auto_data):
        result = build_country_research(sample_auto_data)
        low_conf_modules = [
            "module_05_consumer_psychology",
            "module_06_consumption_preferences",
            "module_08_digital_landscape",
            "module_12_language_communication",
            "module_13_community_social",
            "module_14_marketing_advertising",
            "module_15_competition",
            "module_16_customer_service",
            "module_18_news_current_context",
        ]
        for key in low_conf_modules:
            assert result[key]["confidence"] == "low", f"{key} should be low confidence"

    def test_module_18_news_has_expected_structure(self, sample_auto_data):
        result = build_country_research(sample_auto_data)
        m18 = result["module_18_news_current_context"]
        assert "current_context_summary" in m18
        assert "political_stability" in m18
        assert "confidence" in m18

    def test_module_20_strategic_recommendations_present(self, sample_auto_data):
        result = build_country_research(sample_auto_data)
        m20 = result["module_20_strategic_recommendations"]
        assert "market_entry_strategy" in m20
        assert "pricing_strategy" in m20
        assert "key_success_factors" in m20

    def test_empty_auto_data_still_produces_structure(self):
        result = build_country_research({})
        module_keys = [k for k in result if k.startswith("module_")]
        assert len(module_keys) == 20
        assert result["meta"]["overall_confidence"] in ("medium", "low")

    def test_missing_optional_fields(self, sample_auto_data):
        del sample_auto_data["cities"]
        del sample_auto_data["public_holidays"]
        result = build_country_research(sample_auto_data)
        m2 = result["module_02_demographics"]
        assert m2["top_cities"] == []
        assert m2["cities_count"] == 0

    def test_sources_listed_in_modules(self, sample_auto_data):
        result = build_country_research(sample_auto_data)
        for key, module in result.items():
            if key.startswith("module_"):
                assert "sources" in module, f"{key} missing sources"

    def test_confidence_badges_are_valid(self, sample_auto_data):
        result = build_country_research(sample_auto_data)
        for key in result:
            if key.startswith("module_"):
                conf = result[key].get("confidence", "")
                assert conf in ("high", "medium", "low"), f"{key} has invalid confidence: {conf}"


class TestBuildCountryResearchEdgeCases:
    def test_partial_legal_rules(self, sample_auto_data):
        sample_auto_data["legal_rules"] = {"return_window_days": 7, "minimum_order_age": 18}
        result = build_country_research(sample_auto_data)
        m11 = result["module_11_legal_regulations"]
        assert "7" in m11["mandatory_return_refund_window"]

    def test_no_payment_gateways(self, sample_auto_data):
        sample_auto_data["payment_gateways"] = []
        result = build_country_research(sample_auto_data)
        m9 = result["module_09_payment_infrastructure"]
        assert m9["top_5_payment_gateways"] == []
        assert m9["confidence"] == "low"

    def test_overall_confidence_calculation(self, sample_auto_data):
        result = build_country_research(sample_auto_data)
        # Modules 1,2 are high; 3,7,9,11 are medium; rest are low → overall medium
        assert result["meta"]["overall_confidence"] == "medium"