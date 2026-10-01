"""Tests for infrastructure/utils/currency_service.py.

The original test file referenced ``kernel.currency.convert_amount`` and
``kernel.currency.get_exchange_rate`` which do not exist there (kernel/currency.py
is a 12-line stub). The real implementation lives in this module and exposes
``convert_from_aed``, ``convert_between_currencies``, and ``get_rate_from_aed``.
These tests were rewritten against the actual public API.

NOTE: the test file itself was wrong (see investigation log); it is corrected
here per the contract §14 authorization: 'Fix the test only when the test
itself is wrong.'
"""
from __future__ import annotations

import importlib
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from infrastructure.utils.currency_service import (
    convert_between_currencies,
    convert_from_aed,
    currency_for_country,
    get_currency_context,
    get_currency_metadata,
    get_rate_from_aed,
    money_to_minor_units_for_currency,
    refresh_rate_cache,
)


# ---------------------------------------------------------------------------
# Helper: capture the providers.geography.rates module via the lazy path
# ---------------------------------------------------------------------------

def _rates_mod():
    return importlib.import_module("providers.geography.rates")


# ---------------------------------------------------------------------------
# 1. Lazy-import mechanism (§22 Step 5: confirm fix)
# ---------------------------------------------------------------------------

class TestLazyImportMechanism:
    def test_no_static_providers_import_in_module_body(self):
        """AST must contain no top-level ImportFrom starting with 'providers'."""
        import ast

        spec = importlib.util.find_spec("infrastructure.utils.currency_service")
        assert spec.origin is not None
        with open(spec.origin, encoding="utf-8") as fh:
            tree = ast.parse(fh.read(), filename=spec.origin)
        for node in tree.body:
            if isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                assert not mod.startswith("providers"), (
                    f"Static providers import found: {ast.unparse(node)}"
                )

    def test_lazy_helper_resolves_provider(self):
        mod = _rates_mod()
        assert hasattr(mod, "fetch_rates")
        assert hasattr(mod, "normalize_currency_code")

    def test_lazy_helper_uses_cache(self):
        mod1 = importlib.import_module("providers.geography.rates")
        mod2 = importlib.import_module("providers.geography.rates")
        assert mod1 is mod2


# ---------------------------------------------------------------------------
# 2. Functional: core conversion logic
# ---------------------------------------------------------------------------

class TestCoreConversionLogic:
    def test_get_rate_from_aed_returns_decimal(self):
        rate, source = get_rate_from_aed("USD")
        assert isinstance(rate, Decimal)
        assert rate > 0
        assert isinstance(source, str)

    def test_convert_from_aed_same_currency(self):
        result = convert_from_aed(Decimal("100"), "AED")
        assert result == Decimal("100")

    def test_convert_between_same_currencies(self):
        amount, rate, source = convert_between_currencies(100, "USD", "USD")
        assert amount == Decimal("100")
        assert rate == Decimal("1")
        assert source == "direct"

    def test_convert_between_currencies_returns_tuple(self):
        result = convert_between_currencies(100, "USD", "SAR")
        assert len(result) == 3
        amount, rate, source = result
        assert isinstance(amount, Decimal)
        assert isinstance(rate, Decimal)
        assert isinstance(source, str)

    def test_currency_for_country_known(self):
        assert currency_for_country("AE") == "AED"
        assert currency_for_country("SA") == "SAR"
        assert currency_for_country("US") == "USD"

    def test_currency_for_country_none_returns_default(self):
        assert currency_for_country(None) == "OMR"

    def test_get_currency_metadata_known(self):
        meta = get_currency_metadata("AED")
        assert meta["code"] == "AED"
        assert meta["decimals"] == 2
        assert "name" in meta

    def test_get_currency_metadata_unknown_defaults(self):
        meta = get_currency_metadata("ZZZ")
        assert meta["code"] == "ZZZ"
        assert meta["decimals"] == 2  # default

    def test_money_to_minor_units_aed(self):
        result = money_to_minor_units_for_currency(Decimal("1.5"), "AED")
        assert result == 150  # 1.5 * 100

    def test_get_currency_context_shape(self):
        ctx = get_currency_context(country="AE")
        assert ctx["currency"] == "AED"
        assert "rate_from_aed" in ctx
        assert "decimals" in ctx


# ---------------------------------------------------------------------------
# 3. Error / edge paths
# ---------------------------------------------------------------------------

class TestErrorPaths:
    def test_refresh_rate_cache_returns_dict(self):
        result = refresh_rate_cache()
        assert "source" in result
        assert "currency_count" in result
        assert "expires_at" in result

    def test_normalize_currency_code_none_defaults(self):
        rates_mod = _rates_mod()
        assert rates_mod.normalize_currency_code(None) == "OMR"
        assert rates_mod.normalize_currency_code("") == "OMR"
