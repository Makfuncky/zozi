"""Regression tests for kernel/currency.py pure primitives.

Verifies:
   1. Currency metadata and country-to-currency mapping.
   2. normalize_currency_code pure string normalisation.
   3. convert_from_aed / convert_between_currencies pure arithmetic.
   4. get_rate_from_aed dict lookup and fallback.
   5. money_to_minor_units_for_currency pure rounding.
"""
from __future__ import annotations

from decimal import Decimal

import pytest


class TestCurrencyMetadata:
    def test_known_currency_meta_has_aed(self):
        from kernel.currency import KNOWN_CURRENCY_META

        assert "AED" in KNOWN_CURRENCY_META
        assert KNOWN_CURRENCY_META["AED"]["name"] == "UAE Dirham"
        assert KNOWN_CURRENCY_META["AED"]["decimals"] == 2

    def test_country_to_currency_mapping(self):
        from kernel.currency import COUNTRY_TO_CURRENCY

        assert COUNTRY_TO_CURRENCY["AE"] == "AED"
        assert COUNTRY_TO_CURRENCY["SA"] == "SAR"
        assert COUNTRY_TO_CURRENCY["US"] == "USD"

    def test_get_currency_metadata_unknown_code(self):
        from kernel.currency import get_currency_metadata

        meta = get_currency_metadata("XXX")
        assert meta["code"] == "XXX"
        assert meta["name"] == "XXX"
        assert meta["decimals"] == 2


class TestNormalizeCurrencyCode:
    def test_lowercase_normalized(self):
        from kernel.currency import normalize_currency_code

        assert normalize_currency_code("usd") == "USD"

    def test_mixed_case_and_spaces(self):
        from kernel.currency import normalize_currency_code

        assert normalize_currency_code("  aed  ") == "AED"

    def test_non_alpha_stripped(self):
        from kernel.currency import normalize_currency_code

        assert normalize_currency_code("u-s-d") == "USD"

    def test_short_string_returns_default(self):
        from kernel.currency import normalize_currency_code

        assert normalize_currency_code("U", default="OMR") == "OMR"

    def test_none_returns_default(self):
        from kernel.currency import normalize_currency_code

        assert normalize_currency_code(None) == "OMR"


class TestPureConversionArithmetic:
    def test_convert_from_aed_at_rate_one(self):
        from kernel.currency import convert_from_aed

        result = convert_from_aed(Decimal("100"), Decimal("1"), "AED")
        assert result == Decimal("100.00")

    def test_convert_from_aed_at_half_rate(self):
        from kernel.currency import convert_from_aed

        result = convert_from_aed(Decimal("100"), Decimal("0.5"), "USD")
        assert result == Decimal("50.00")

    def test_convert_from_aed_rounds_up(self):
        from kernel.currency import convert_from_aed

        result = convert_from_aed(Decimal("1"), Decimal("0.27225"), "USD")
        assert result == Decimal("0.27")

    def test_convert_between_currencies_same_code(self):
        from kernel.currency import convert_between_currencies

        converted, rate, source = convert_between_currencies(
            Decimal("100"), Decimal("1"), Decimal("1"), "AED", "AED"
        )
        assert converted == Decimal("100.00")
        assert rate == Decimal("1")
        assert source == "direct"

    def test_convert_between_currencies_different(self):
        from kernel.currency import convert_between_currencies

        converted, rate, source = convert_between_currencies(
            Decimal("100"), Decimal("1"), Decimal("0.27225"), "AED", "USD"
        )
        assert converted == Decimal("27.23")
        assert rate == Decimal("0.272250")

    def test_get_rate_from_aed_hit(self):
        from kernel.currency import get_rate_from_aed

        rates = {"USD": Decimal("0.27225"), "SAR": Decimal("1.0208")}
        rate, source = get_rate_from_aed(rates, "USD")
        assert rate == Decimal("0.27225")
        assert source == "direct"

    def test_get_rate_from_aed_miss_fallback(self):
        from kernel.currency import get_rate_from_aed

        rates = {"USD": Decimal("0.27225")}
        rate, source = get_rate_from_aed(rates, "XXX")
        assert source == "fallback"
        assert rate == Decimal("1")

    def test_money_to_minor_units_for_currency(self):
        from kernel.currency import money_to_minor_units_for_currency

        result = money_to_minor_units_for_currency(Decimal("1.00"), Decimal("1"), "USD")
        assert result == 100

    def test_money_to_minor_units_three_decimals(self):
        from kernel.currency import money_to_minor_units_for_currency

        result = money_to_minor_units_for_currency(Decimal("1.000"), Decimal("1"), "OMR")
        assert result == 1000
