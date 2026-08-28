"""Smoke tests for the kernel primitives.

Verifies:
  1. Money/Decimal operations (to_decimal, round_money, to_cents, from_cents).
  2. Currency conversion primitives.
  3. Numbering sequences (next_reference).
  4. Country primitives (CountryCode, normalize_country).
  5. Period primitives (fiscal_quarter, date_range).
"""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import pytest


class TestMoneyOperations:
    """Money primitives use Decimal, never float."""

    def test_to_decimal_from_float(self):
        from kernel.money import to_decimal
        result = to_decimal(10.50)
        assert isinstance(result, Decimal)
        assert result == Decimal("10.5")

    def test_to_decimal_from_string(self):
        from kernel.money import to_decimal
        result = to_decimal("99.99")
        assert result == Decimal("99.99")

    def test_to_decimal_from_decimal(self):
        from kernel.money import to_decimal
        val = Decimal("42.00")
        result = to_decimal(val)
        assert result == val

    def test_to_decimal_none_returns_default(self):
        from kernel.money import to_decimal
        result = to_decimal(None)
        assert result == Decimal("0.00")

    def test_to_decimal_invalid_returns_default(self):
        from kernel.money import to_decimal
        result = to_decimal("not-a-number")
        assert result == Decimal("0.00")

    def test_round_money(self):
        from kernel.money import round_money
        result = round_money(Decimal("10.555"))
        assert result == Decimal("10.56")

    def test_round_money_custom_places(self):
        from kernel.money import round_money
        result = round_money(Decimal("10.55555"), places="0.001")
        assert result == Decimal("10.556")

    def test_to_cents(self):
        from kernel.money import to_cents
        assert to_cents(Decimal("1.00")) == 100
        assert to_cents(Decimal("0.99")) == 99
        assert to_cents(Decimal("10.50")) == 1050

    def test_from_cents(self):
        from kernel.money import from_cents
        assert from_cents(100) == Decimal("1.00")
        assert from_cents(99) == Decimal("0.99")
        assert from_cents(0) == Decimal("0.00")

    def test_money_to_minor_units_alias(self):
        from kernel.money import money_to_minor_units, to_cents
        assert money_to_minor_units(Decimal("1.00")) == to_cents(Decimal("1.00"))

    def test_format_currency(self):
        from kernel.money import format_currency
        result = format_currency(Decimal("42.50"), "USD")
        assert result == "USD 42.50"

    def test_format_currency_default(self):
        from kernel.money import format_currency
        result = format_currency(Decimal("100.00"))
        assert result == "USD 100.00"

    def test_money_quant_constant(self):
        from kernel.money import MONEY_QUANT
        assert MONEY_QUANT == Decimal("0.01")


class TestCurrencyPrimitives:
    """Currency primitives are pure and provider-independent."""

    def test_currency_module_importable(self):
        import kernel.currency
        assert kernel.currency is not None

    def test_currency_module_has_no_provider_deps(self):
        """Kernel currency must not import from providers."""
        import kernel.currency as mod
        source = open(mod.__file__).read()
        assert "providers" not in source


class TestNumberingSequences:
    """Reference numbering for business documents."""

    def test_next_reference_order(self):
        from kernel.numbering import next_reference
        ref = next_reference("order", seq=1)
        assert ref == "ORD-000001"

    def test_next_reference_invoice(self):
        from kernel.numbering import next_reference
        ref = next_reference("invoice", seq=42)
        assert ref == "INV-000042"

    def test_next_reference_payout(self):
        from kernel.numbering import next_reference
        ref = next_reference("payout", seq=100)
        assert ref == "PAY-000100"

    def test_next_reference_batch(self):
        from kernel.numbering import next_reference
        ref = next_reference("batch", seq=5)
        assert ref == "BATCH-000005"

    def test_next_reference_with_country(self):
        from kernel.numbering import next_reference
        ref = next_reference("order", country="AE", seq=1)
        assert ref == "ORD-000001-AE"

    def test_next_reference_unknown_kind(self):
        from kernel.numbering import next_reference
        ref = next_reference("unknown_type", seq=1)
        assert ref.startswith("UNKN-")

    def test_next_reference_auto_sequence(self):
        from kernel.numbering import next_reference
        ref1 = next_reference("order")
        ref2 = next_reference("order")
        assert ref1 != ref2


class TestCountryPrimitives:
    """Country code typing and normalization."""

    def test_country_code_type(self):
        from kernel.country import CountryCode
        code = CountryCode("AE")
        assert isinstance(code, str)
        assert code == "AE"

    def test_normalize_country_uppercase(self):
        from kernel.country import normalize_country
        result = normalize_country("ae")
        assert result == "AE"

    def test_normalize_country_strips_whitespace(self):
        from kernel.country import normalize_country
        result = normalize_country("  US  ")
        assert result == "US"

    def test_normalize_country_returns_country_code_type(self):
        from kernel.country import CountryCode, normalize_country
        result = normalize_country("SA")
        assert isinstance(result, CountryCode)


class TestPeriodPrimitives:
    """Fiscal period and date-range logic."""

    def test_fiscal_quarter_q1(self):
        from kernel.period import fiscal_quarter
        assert fiscal_quarter(date(2024, 1, 15)) == 1
        assert fiscal_quarter(date(2024, 2, 1)) == 1
        assert fiscal_quarter(date(2024, 3, 31)) == 1

    def test_fiscal_quarter_q2(self):
        from kernel.period import fiscal_quarter
        assert fiscal_quarter(date(2024, 4, 1)) == 2
        assert fiscal_quarter(date(2024, 6, 30)) == 2

    def test_fiscal_quarter_q3(self):
        from kernel.period import fiscal_quarter
        assert fiscal_quarter(date(2024, 7, 1)) == 3
        assert fiscal_quarter(date(2024, 9, 30)) == 3

    def test_fiscal_quarter_q4(self):
        from kernel.period import fiscal_quarter
        assert fiscal_quarter(date(2024, 10, 1)) == 4
        assert fiscal_quarter(date(2024, 12, 31)) == 4

    def test_date_range(self):
        from kernel.period import date_range
        start = date(2024, 1, 1)
        end = date(2024, 1, 5)
        result = list(date_range(start, end))
        assert len(result) == 5
        assert result[0] == start
        assert result[-1] == end

    def test_date_range_single_day(self):
        from kernel.period import date_range
        d = date(2024, 6, 15)
        result = list(date_range(d, d))
        assert result == [d]

    def test_date_range_empty(self):
        from kernel.period import date_range
        start = date(2024, 1, 5)
        end = date(2024, 1, 1)
        result = list(date_range(start, end))
        assert result == []
