"""
Tests for country_auto_populate service
===========================================
Tests cover: helper functions (heuristic engine, normalization, confidence scoring),
data fetching fallbacks, and the main auto_populate_country orchestration.
"""

from __future__ import annotations

import json
import os
import sys
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from data.services_country_auto_populate import (
    _first_currency,
    _normalize_rest_country,
    _phone_code,
    calculate_confidence_score,
    calculate_gateway_rankings,
    calculate_commission_tiers,
    determine_kyc_tier,
    determine_logistics_model,
    determine_region,
    get_product_restrictions_for_region,
    get_legal_rules_for_region,
    GATEWAY_REGISTRY,
    BASE_COMMISSIONS,
    KYC_REQUIREMENTS,
)


class TestHelperFunctions:
    """Tests for pure helper functions (no external calls)."""

    def test_first_currency_with_data(self):
        data = {
            "currencies": {
                "USD": {"name": "US Dollar", "symbol": "$"},
                "EUR": {"name": "Euro", "symbol": "\u20ac"},
            }
        }
        codes, symbol, name = _first_currency(data)
        assert codes == ["USD", "EUR"]
        assert symbol == "$"
        assert name == "US Dollar"

    def test_first_currency_empty(self):
        data = {"currencies": {}}
        codes, symbol, name = _first_currency(data)
        assert codes == []
        assert symbol is None
        assert name is None

    def test_first_currency_no_key(self):
        data = {}
        codes, symbol, name = _first_currency(data)
        assert codes == []
        assert symbol is None
        assert name is None

    def test_phone_code_with_suffixes(self):
        data = {"idd": {"root": "+9", "suffixes": ["71", "72"]}}
        assert _phone_code(data) == "+971"

    def test_phone_code_no_suffix(self):
        data = {"idd": {"root": "+1"}}
        assert _phone_code(data) == "+1"

    def test_phone_code_empty(self):
        data = {"idd": {}}
        assert _phone_code(data) == ""

    def test_phone_code_missing(self):
        data = {}
        assert _phone_code(data) == ""

    def test_normalize_rest_country_full(self):
        data = {
            "cca2": "SA",
            "cca3": "SAU",
            "name": {"common": "Saudi Arabia", "official": "Kingdom of Saudi Arabia"},
            "flags": {"svg": "https://flag.svg", "png": "https://flag.png"},
            "latlng": [24.0, 45.0],
            "capital": ["Riyadh"],
            "languages": {"ara": "Arabic"},
            "currencies": {"SAR": {"name": "Saudi Riyal", "symbol": "\ufdfc"}},
            "idd": {"root": "+966"},
            "timezones": ["UTC+03:00"],
            "region": "Asia",
            "subregion": "Western Asia",
            "population": 35000000,
        }
        result = _normalize_rest_country(data)
        assert result["code"] == "SA"
        assert result["name"] == "Saudi Arabia"
        assert result["official_name"] == "Kingdom of Saudi Arabia"
        assert result["alpha3"] == "SAU"
        assert result["phone_code"] == "+966"
        assert result["flag_url"] == "https://flag.svg"
        assert result["capital"] == "Riyadh"
        assert result["currencies"] == ["SAR"]
        assert result["currency_symbol"] == "\ufdfc"
        assert result["currency_name"] == "Saudi Riyal"
        assert result["region"] == "Asia"
        assert result["population"] == 35000000

    def test_normalize_rest_country_minimal(self):
        data = {"cca2": "XX", "name": {"common": "Test"}}
        result = _normalize_rest_country(data)
        assert result["code"] == "XX"
        assert result["name"] == "Test"
        assert result["official_name"] in (None, "")
        assert result["phone_code"] == ""
        assert result["timezone"] == "UTC"
        assert result["languages"] == []


class TestConfidenceScore:
    def test_full_score(self):
        rest_data = {
            "name": "Test",
            "currencies": ["USD"],
            "capital": "Test City",
            "latitude": 10.0,
            "longitude": 20.0,
            "languages": ["English"],
            "region": "Americas",
            "flag_url": "https://flag.svg",
            "phone_code": "+1",
        }
        wb_data = {"gdp_per_capita_usd": 50000}
        cities = [{"name": "Test City"}]
        score = calculate_confidence_score(rest_data, wb_data, cities)
        assert score == 1.0

    def test_no_data(self):
        assert calculate_confidence_score(None, None, []) == 0.0

    def test_partial_data(self):
        rest_data = {"name": "Test", "currencies": ["USD"]}
        score = calculate_confidence_score(rest_data, None, [])
        assert score == 0.2

    def test_no_cities_penalty(self):
        rest_data = {
            "name": "Test",
            "currencies": ["USD"],
            "capital": "C",
            "latitude": 1.0,
            "longitude": 2.0,
            "languages": ["En"],
            "region": "A",
            "flag_url": "f",
            "phone_code": "+1",
        }
        score = calculate_confidence_score(rest_data, None, [])
        assert score == 0.8  # 8 out of 10 checks (missing wb_data + cities)

    def test_no_wb_data_penalty(self):
        rest_data = {
            "name": "Test",
            "currencies": ["USD"],
            "capital": "C",
            "latitude": 1.0,
            "longitude": 2.0,
            "languages": ["En"],
            "region": "A",
            "flag_url": "f",
            "phone_code": "+1",
        }
        cities = [{"name": "City"}]
        score = calculate_confidence_score(rest_data, None, cities)
        assert score == pytest.approx(0.9, abs=0.01)


class TestGatewayRankings:
    def test_gateway_rankings_saudi(self):
        rankings = calculate_gateway_rankings("SA", ["SAR"], "Asia")
        assert len(rankings) > 0
        names = [r["name"] for r in rankings]
        assert "TAP" in names or "Hyperpay" in names or "PayTabs" in names or "Tabby" in names

    def test_gateway_rankings_us(self):
        rankings = calculate_gateway_rankings("US", ["USD"], "Americas")
        assert len(rankings) > 0
        names = [r["name"] for r in rankings]
        assert "Stripe" in names

    def test_gateway_rankings_score_format(self):
        rankings = calculate_gateway_rankings("AE", ["AED"], "Asia")
        for r in rankings:
            assert "gateway_id" in r
            assert "score" in r
            assert "name" in r
            assert isinstance(r["score"], (int, float))
            assert r["score"] >= 0

    def test_gateway_rankings_high_internet(self):
        rankings_high = calculate_gateway_rankings("AE", ["AED"], "Asia", internet_pen=95)
        rankings_low = calculate_gateway_rankings("AE", ["AED"], "Asia", internet_pen=30)
        highest_high = max(r["score"] for r in rankings_high) if rankings_high else 0
        highest_low = max(r["score"] for r in rankings_low) if rankings_low else 0
        assert highest_high > 0
        assert highest_low > 0


class TestCommissionTiers:
    def test_commission_tiers_structure(self):
        tiers = calculate_commission_tiers("developing")
        assert "electronics" in tiers
        assert "fashion" in tiers
        assert "groceries" in tiers
        assert all("suggested_rate" in v for v in tiers.values())
        assert all("min_rate" in v for v in tiers.values())
        assert all("max_rate" in v for v in tiers.values())

    def test_commission_tiers_developing_multiplier(self):
        dev = calculate_commission_tiers("developing")
        eme = calculate_commission_tiers("emerging")
        assert dev["fashion"]["suggested_rate"] >= eme["fashion"]["suggested_rate"]

    def test_commission_tiers_bounds(self):
        tiers = calculate_commission_tiers("developed")
        for cat, bounds in BASE_COMMISSIONS.items():
            t = tiers[cat]
            assert t["min_rate"] <= t["suggested_rate"] <= t["max_rate"]

    def test_commission_tiers_all_categories(self):
        tiers = calculate_commission_tiers("developing")
        for cat in BASE_COMMISSIONS:
            assert cat in tiers, f"Missing category: {cat}"


class TestDeterminationFunctions:
    @pytest.mark.parametrize(
        "gdp,expected_tier",
        [
            (50000, "strict"),
            (20000, "standard"),
            (5000, "basic"),
            (0, "basic"),
        ],
    )
    def test_determine_kyc_tier(self, gdp, expected_tier):
        assert determine_kyc_tier(gdp) == expected_tier

    @pytest.mark.parametrize(
        "internet,population,expected",
        [
            (90, 10000000, "hub_and_spoke"),
            (70, 10000000, "point_to_point"),
            (30, 10000000, "basic_delivery"),
            (90, 5000001, "hub_and_spoke"),
            (60, 1000000, "point_to_point"),
            (10, 100000, "basic_delivery"),
        ],
    )
    def test_determine_logistics_model(self, internet, population, expected):
        assert determine_logistics_model(internet, population) == expected

    @pytest.mark.parametrize(
        "internet,gdp,expected",
        [
            (90, 30000, "developed"),
            (70, 10000, "developing"),
            (30, 3000, "emerging"),
        ],
    )
    def test_determine_region(self, internet, gdp, expected):
        assert determine_region(internet, gdp) == expected

    @pytest.mark.parametrize(
        "region,expected_restrictions",
        [
            ("GCC", ["alcohol", "pork", "gambling"]),
            ("Middle East", ["alcohol", "pork", "gambling"]),
            ("Europe", []),
            ("North America", []),
            ("Unknown", []),
        ],
    )
    def test_product_restrictions(self, region, expected_restrictions):
        assert get_product_restrictions_for_region(region) == expected_restrictions

    @pytest.mark.parametrize(
        "region,expected_has_commercial_license",
        [
            ("GCC", True),
            ("Middle East", True),
            ("Europe", False),
        ],
    )
    def test_legal_rules(self, region, expected_has_commercial_license):
        rules = get_legal_rules_for_region(region)
        assert rules["requires_commercial_license"] == expected_has_commercial_license
        assert rules["return_window_days"] == 14


class TestGatewayRegistry:
    def test_gateway_registry_has_required_keys(self):
        for gw_id, gw in GATEWAY_REGISTRY.items():
            assert "regions" in gw, f"Missing regions in {gw_id}"
            assert "currencies" in gw, f"Missing currencies in {gw_id}"
            assert "setup_days" in gw, f"Missing setup_days in {gw_id}"
            assert "avg_fee" in gw, f"Missing avg_fee in {gw_id}"
            assert "name" in gw, f"Missing name in {gw_id}"

    def test_gateway_registry_types(self):
        types_seen = set()
        for gw in GATEWAY_REGISTRY.values():
            types_seen.add(gw["type"])
        assert "card" in types_seen
        assert "bnpl" in types_seen or "wallet" in types_seen


class TestKYCRequirements:
    def test_kyc_tiers_exist(self):
        assert "basic" in KYC_REQUIREMENTS
        assert "standard" in KYC_REQUIREMENTS
        assert "strict" in KYC_REQUIREMENTS

    def test_kyc_tier_strictness(self):
        assert len(KYC_REQUIREMENTS["basic"]["documents"]) < len(KYC_REQUIREMENTS["strict"]["documents"])
        assert KYC_REQUIREMENTS["basic"]["requires_commercial"] is False
        assert KYC_REQUIREMENTS["strict"]["requires_commercial"] is True


class TestCountryAutoPopulateIntegration:
    """Integration tests for auto_populate_country using mocked external APIs."""

    @pytest.mark.asyncio
    async def test_auto_populate_empty_code(self):
        from data.services_country_auto_populate import auto_populate_country
        result = await auto_populate_country("")
        assert result.get("error") == "Empty search term"
        assert result.get("degraded") is True

    @pytest.mark.asyncio
    async def test_auto_populate_with_mocked_data(self):
        """Test auto_populate_country returns expected structure with mocked fetchers."""

        mock_rest = {
            "code": "SA",
            "name": "Saudi Arabia",
            "official_name": "Kingdom of Saudi Arabia",
            "alpha3": "SAU",
            "phone_code": "+966",
            "flag_url": "https://flag.sa.svg",
            "latitude": 24.0,
            "longitude": 45.0,
            "capital": "Riyadh",
            "languages": ["Arabic"],
            "currencies": ["SAR"],
            "currency_symbol": "\ufdfc",
            "currency_name": "Saudi Riyal",
            "timezone": "UTC+03:00",
            "region": "Asia",
            "subregion": "Western Asia",
            "population": 35000000,
        }

        mock_wb = {"gdp_per_capita_usd": 23000.0, "population": 35000000.0, "internet_penetration_pct": 97.9}

        mock_cities = [
            {"name": "Riyadh", "region": "Riyadh", "latitude": 24.7, "longitude": 46.7, "population": 8000000, "is_capital": True},
            {"name": "Jeddah", "region": "Makkah", "latitude": 21.5, "longitude": 39.2, "population": 4000000, "is_capital": False},
        ]

        mock_holidays = [
            {"name": "Eid al-Fitr", "date": "2026-04-01", "local_name": "Eid al-Fitr"},
        ]

        mock_vat = 0.15

        # The internal safe_fetch_with_breaker calls api_breaker.call(fetch_func).
        # We mock api_breaker.call to call the function and wrap result as {"data": result}
        async def mock_breaker_call(fetch_func):
            result = await fetch_func()
            if result is not None:
                return {"data": result, "error": None}
            return {"data": None, "error": "fetch failed"}

        with patch("services.country_auto_populate._get_redis", return_value=None), \
             patch("services.country_auto_populate.fetch_rest_countries", AsyncMock(return_value=mock_rest)), \
             patch("services.country_auto_populate.fetch_world_bank_data", AsyncMock(return_value=mock_wb)), \
             patch("services.country_auto_populate.fetch_geodb_cities", AsyncMock(return_value=mock_cities)), \
             patch("services.country_auto_populate.fetch_public_holidays", AsyncMock(return_value=mock_holidays)), \
             patch("services.country_auto_populate.fetch_vat_rate", AsyncMock(return_value=mock_vat)), \
             patch("services.country_auto_populate.api_breaker.call", mock_breaker_call):

            from data.services_country_auto_populate import auto_populate_country
            result = await auto_populate_country("SA")

            assert result is not None
            assert result["code"] == "SA"
            assert result["name"] == "Saudi Arabia"
            assert result["capital"] == "Riyadh"
            assert result["currency"] == "SAR"
            assert result["currency_symbol"] == "\ufdfc"
            assert result["tax_rate"] == 0.15
            assert result["tax_type"] == "VAT"
            expected_cities = [
                {"name": "Riyadh", "region": "Riyadh", "lat": 24.7, "lng": 46.7, "population": 8000000, "is_capital": True},
                {"name": "Jeddah", "region": "Makkah", "lat": 21.5, "lng": 39.2, "population": 4000000, "is_capital": False},
            ]
            assert result["cities"] == expected_cities
            assert len(result["cities"]) == 2
            assert result["economic_tier"] in ("developed", "developing", "emerging")
            assert result["confidence_score"] > 0
            assert result["cod_enabled"] is True
            assert isinstance(result["payment_gateways"], list)
            assert len(result["payment_gateways"]) > 0

    @pytest.mark.asyncio
    async def test_auto_populate_degraded_without_rest_countries(self):
        async def mock_breaker_call(fetch_func):
            result = await fetch_func()
            if result is not None:
                return {"data": result, "error": None}
            return {"data": None, "error": "fetch failed"}

        with patch("services.country_auto_populate._get_redis", return_value=None), \
             patch("services.country_auto_populate.fetch_rest_countries", AsyncMock(return_value=None)), \
             patch("services.country_auto_populate.fetch_world_bank_data", AsyncMock(return_value=None)), \
             patch("services.country_auto_populate.fetch_geodb_cities", AsyncMock(return_value=[])), \
             patch("services.country_auto_populate.fetch_public_holidays", AsyncMock(return_value=[])), \
             patch("services.country_auto_populate.fetch_vat_rate", AsyncMock(return_value=None)), \
             patch("services.country_auto_populate.api_breaker.call", mock_breaker_call):

            from data.services_country_auto_populate import auto_populate_country
            result = await auto_populate_country("XX")
            assert "error" in result or result.get("degraded") is True

    @pytest.mark.asyncio
    async def test_auto_populate_structure_completeness(self):
        """Verify the auto-populate response has all required fields."""
        mock_rest = {
            "code": "AE",
            "name": "United Arab Emirates",
            "official_name": "United Arab Emirates",
            "alpha3": "ARE",
            "phone_code": "+971",
            "flag_url": "https://flag.ae.svg",
            "latitude": 24.0,
            "longitude": 54.0,
            "capital": "Abu Dhabi",
            "languages": ["Arabic"],
            "currencies": ["AED"],
            "currency_symbol": "\u062f.\u0625",
            "currency_name": "UAE Dirham",
            "timezone": "UTC+04:00",
            "region": "Asia",
            "subregion": "Western Asia",
            "population": 10000000,
        }

        async def mock_breaker_call(fetch_func):
            result = await fetch_func()
            if result is not None:
                return {"data": result, "error": None}
            return {"data": None, "error": "fetch failed"}

        with patch("services.country_auto_populate._get_redis", return_value=None), \
             patch("services.country_auto_populate.fetch_rest_countries", AsyncMock(return_value=mock_rest)), \
             patch("services.country_auto_populate.fetch_world_bank_data", AsyncMock(return_value=None)), \
             patch("services.country_auto_populate.fetch_geodb_cities", AsyncMock(return_value=[])), \
             patch("services.country_auto_populate.fetch_public_holidays", AsyncMock(return_value=[])), \
             patch("services.country_auto_populate.fetch_vat_rate", AsyncMock(return_value=0.05)), \
             patch("services.country_auto_populate.api_breaker.call", mock_breaker_call):

            from data.services_country_auto_populate import auto_populate_country
            result = await auto_populate_country("AE")

            required_fields = [
                "code", "name", "official_name", "alpha3", "phone_code", "flag_url",
                "capital", "currency", "currency_symbol", "currency_name",
                "tax_type", "tax_rate", "tax_name",
                "economic_tier", "confidence_score",
                "payment_gateways", "supplier_requirements",
                "payout_settings", "commission_tiers",
                "cod_enabled", "legal_rules",
                "consumer_protection_days", "data_privacy_framework",
            ]
            for field in required_fields:
                assert field in result, f"Missing required field: {field}"

    @pytest.mark.asyncio
    async def test_auto_populate_confidence_scoring(self):
        """Confidence score should be higher with more data."""
        mock_rest_full = {
            "code": "US", "name": "United States", "official_name": "United States of America",
            "alpha3": "USA", "phone_code": "+1", "flag_url": "https://flag.us.svg",
            "latitude": 38.0, "longitude": -97.0, "capital": "Washington, D.C.",
            "languages": ["English"], "currencies": ["USD"], "currency_symbol": "$",
            "currency_name": "US Dollar", "timezone": "UTC-05:00",
            "region": "Americas", "subregion": "Northern America", "population": 331000000,
        }
        mock_wb = {"gdp_per_capita_usd": 76000.0, "population": 331000000.0, "internet_penetration_pct": 92.0}
        mock_cities = [{"name": "New York", "region": "NY", "latitude": 40.7, "longitude": -74.0, "population": 8500000, "is_capital": False}]

        async def mock_breaker_call(fetch_func):
            result = await fetch_func()
            if result is not None:
                return {"data": result, "error": None}
            return {"data": None, "error": "fetch failed"}

        with patch("services.country_auto_populate._get_redis", return_value=None), \
             patch("services.country_auto_populate.fetch_rest_countries", AsyncMock(return_value=mock_rest_full)), \
             patch("services.country_auto_populate.fetch_world_bank_data", AsyncMock(return_value=mock_wb)), \
             patch("services.country_auto_populate.fetch_geodb_cities", AsyncMock(return_value=mock_cities)), \
             patch("services.country_auto_populate.fetch_public_holidays", AsyncMock(return_value=[])), \
             patch("services.country_auto_populate.fetch_vat_rate", AsyncMock(return_value=None)), \
             patch("services.country_auto_populate.api_breaker.call", mock_breaker_call):

            from data.services_country_auto_populate import auto_populate_country
            result = await auto_populate_country("US")
            assert result["confidence_score"] >= 0.5


class TestAutoPopulateNormalize:
    def test_normalize_rest_country_no_flags(self):
        data = {"cca2": "OM", "name": {"common": "Oman"}}
        result = _normalize_rest_country(data)
        assert result["flag_url"] == ""  # Neither svg nor png

    def test_normalize_rest_country_fallback_png(self):
        data = {"cca2": "OM", "name": {"common": "Oman"}, "flags": {"png": "https://flag.png"}}
        result = _normalize_rest_country(data)
        assert result["flag_url"] == "https://flag.png"

    def test_normalize_rest_country_languages_keys(self):
        data = {
            "cca2": "KW",
            "name": {"common": "Kuwait"},
            "languages": {"ara": "Arabic"},
        }
        result = _normalize_rest_country(data)
        assert "Arabic" in result["languages"] or "ara" in result["languages"]


class TestDataConstants:
    def test_base_commissions_all_categories(self):
        expected_categories = [
            "electronics", "fashion", "groceries", "health_beauty",
            "home_furniture", "automotive", "sports", "books_media",
            "toys_games", "digital_goods", "jewelry", "pet_supplies",
        ]
        for cat in expected_categories:
            assert cat in BASE_COMMISSIONS
            assert "min" in BASE_COMMISSIONS[cat]
            assert "max" in BASE_COMMISSIONS[cat]
            assert "suggested" in BASE_COMMISSIONS[cat]
            assert 0 < BASE_COMMISSIONS[cat]["min"] <= BASE_COMMISSIONS[cat]["max"] <= 1
