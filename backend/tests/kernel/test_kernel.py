"""Law-aligned tests for the shared kernel (pure business primitives).

Laws covered:
  - Law 10 / 101: kernel/ imports NOTHING from domains/modules/rbac/providers/jobs/middleware
  - Law 19: money uses Decimal, never float
  - Law 20: country validation (ISO 3166 alpha-2)
  - Law 1: arrows point down only (kernel may use platform primitives only)
"""
from __future__ import annotations

import ast
import os
import sys
from decimal import Decimal
from pathlib import Path

import pytest

# Ensure backend root is importable
_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

# --- Inlined from tests._support.laws (import path broken in this env) ---

FORBIDDEN_IMPORT_RULES: dict[str, tuple[str, ...]] = {
    "domains": ("modules", "rbac"),
    "infrastructure": ("domains", "modules", "rbac", "providers"),
    "kernel": ("domains", "modules", "rbac", "providers", "infrastructure", "jobs", "middleware"),
    "providers": ("domains", "modules", "rbac", "jobs", "middleware"),
    "jobs": ("modules", "middleware"),
    "middleware": ("domains", "modules"),
}


def _read_source(module_path: Path) -> ast.Module:
    return ast.parse(module_path.read_text(encoding="utf-8"), filename=str(module_path))


def _module_import_roots(tree: ast.Module) -> list[str]:
    roots: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.append(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                roots.append(node.module.split(".")[0])
    return roots


def assert_no_forbidden_imports(package_root: str, source_dir: Path) -> None:
    forbidden = FORBIDDEN_IMPORT_RULES.get(package_root, ())
    if not forbidden:
        return
    violations: list[str] = []
    for path in sorted(source_dir.rglob("*.py")):
        if path.name == "__init__.py":
            continue
        try:
            tree = _read_source(path)
        except SyntaxError as exc:
            violations.append(f"{path}: syntax error ({exc})")
            continue
        for root in _module_import_roots(tree):
            if root in forbidden:
                violations.append(f"{path}: imports forbidden layer '{root}'")
    assert not violations, (
        f"{package_root} violates Law 1 (arrows point down only):\n"
        + "\n".join(f"  - {v}" for v in violations)
    )


BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
KERNEL_DIR = BACKEND_ROOT / "kernel"


class TestKernelPurity:
    """Law 10 / 101: kernel/ must not import forbidden layers."""

    def test_kernel_no_forbidden_imports(self) -> None:
        assert_no_forbidden_imports("kernel", KERNEL_DIR)

    def test_kernel_imports_only_stdlib_and_infra(self) -> None:
        """Verify kernel modules only import stdlib or infrastructure."""
        allowed_roots = {"decimal", "typing", "datetime", "time", "infrastructure"}
        for path in sorted(KERNEL_DIR.rglob("*.py")):
            if path.name == "__init__.py":
                continue
            tree = _read_source(path)
            roots = _module_import_roots(tree)
            forbidden = [r for r in roots if r not in allowed_roots and not r.startswith("_")]
            assert not forbidden, f"{path} imports unexpected roots: {forbidden}"


class TestMoneyPrimitives:
    """Law 19: money uses Decimal, never float."""

    def test_to_decimal_from_string(self) -> None:
        from kernel.money import to_decimal
        result = to_decimal("10.50")
        assert result == Decimal("10.50")
        assert isinstance(result, Decimal)

    def test_to_decimal_from_float_uses_str(self) -> None:
        """Converting from float must go through str() to avoid float artifacts."""
        from kernel.money import to_decimal
        result = to_decimal(0.1)
        assert isinstance(result, Decimal)
        assert result == Decimal("0.1")

    def test_to_decimal_from_decimal_passthrough(self) -> None:
        from kernel.money import to_decimal
        d = Decimal("99.99")
        assert to_decimal(d) is d

    def test_to_decimal_none_returns_default(self) -> None:
        from kernel.money import to_decimal
        assert to_decimal(None) == Decimal("0.00")

    def test_to_decimal_invalid_returns_default(self) -> None:
        from kernel.money import to_decimal
        assert to_decimal("not-a-number") == Decimal("0.00")

    def test_round_money_half_up(self) -> None:
        from kernel.money import round_money
        assert round_money("10.005") == Decimal("10.01")
        assert round_money("10.004") == Decimal("10.00")

    def test_to_cents(self) -> None:
        from kernel.money import to_cents
        assert to_cents("1.50") == 150
        assert to_cents(Decimal("10.99")) == 1099

    def test_from_cents(self) -> None:
        from kernel.money import from_cents
        assert from_cents(150) == Decimal("1.50")
        assert from_cents(0) == Decimal("0.00")

    def test_money_to_minor_units_alias(self) -> None:
        from kernel.money import money_to_minor_units, to_cents
        assert money_to_minor_units("2.50") == to_cents("2.50")

    def test_format_currency(self) -> None:
        from kernel.money import format_currency
        assert format_currency("10.50", "USD") == "USD 10.50"
        assert format_currency(Decimal("100"), "EUR") == "EUR 100.00"

    def test_money_quant_is_decimal(self) -> None:
        from kernel.money import MONEY_QUANT
        assert isinstance(MONEY_QUANT, Decimal)
        assert MONEY_QUANT == Decimal("0.01")

    def test_no_float_in_money_module(self) -> None:
        """Scan money.py source for float literals (Law 19)."""
        source = (KERNEL_DIR / "money.py").read_text()
        # Check for float literals like 0.0, 1.0, etc. (not in strings)
        import re
        float_pattern = re.compile(r'\b\d+\.\d+\b')
        # Exclude comments and string literals
        lines = []
        for i, line in enumerate(source.split("\n"), 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            # Remove string literals
            cleaned = re.sub(r'["\'][^"\']*["\']', '""', line)
            if float_pattern.search(cleaned):
                lines.append(f"{i}: {stripped}")
        assert not lines, f"Float literals found in money.py: {lines}"


class TestNumbering:
    """Centralized reference numbering (ORD-, INV-, PAY-, BATCH-)."""

    def test_next_reference_order(self) -> None:
        from kernel.numbering import next_reference
        ref = next_reference("order", seq=1)
        assert ref.startswith("ORD-")
        assert "000001" in ref

    def test_next_reference_invoice(self) -> None:
        from kernel.numbering import next_reference
        ref = next_reference("invoice", seq=42)
        assert ref.startswith("INV-")
        assert "000042" in ref

    def test_next_reference_payout(self) -> None:
        from kernel.numbering import next_reference
        ref = next_reference("payout", seq=999)
        assert ref.startswith("PAY-")

    def test_next_reference_batch(self) -> None:
        from kernel.numbering import next_reference
        ref = next_reference("batch", seq=1)
        assert ref.startswith("BATCH-")

    def test_next_reference_with_country(self) -> None:
        from kernel.numbering import next_reference
        ref = next_reference("order", country="AE", seq=1)
        assert ref.endswith("-AE")

    def test_next_reference_unknown_kind(self) -> None:
        from kernel.numbering import next_reference
        ref = next_reference("unknown", seq=1)
        assert ref.startswith("UNKN-")

    def test_next_reference_unique_with_seq(self) -> None:
        """When explicit seq is provided, references are unique."""
        from kernel.numbering import next_reference
        refs = {next_reference("order", seq=i) for i in range(100)}
        assert len(refs) == 100


class TestCountryPrimitives:
    """Law 20: country validation (ISO 3166 alpha-2)."""

    def test_normalize_country_uppercase(self) -> None:
        from kernel.country import normalize_country
        assert normalize_country("ae") == "AE"
        assert normalize_country("us") == "US"

    def test_normalize_country_strips_whitespace(self) -> None:
        from kernel.country import normalize_country
        assert normalize_country("  AE  ") == "AE"

    def test_country_code_is_string(self) -> None:
        from kernel.country import CountryCode, normalize_country
        code = normalize_country("SA")
        assert isinstance(code, str)
        assert code == "SA"

    def test_country_code_newtype(self) -> None:
        from kernel.country import CountryCode
        assert CountryCode.__supertype__ is str


class TestPeriodPrimitives:
    """Fiscal period / date-range logic."""

    def test_fiscal_quarter_q1(self) -> None:
        from kernel.period import fiscal_quarter
        from datetime import date
        assert fiscal_quarter(date(2026, 1, 15)) == 1
        assert fiscal_quarter(date(2026, 3, 31)) == 1

    def test_fiscal_quarter_q2(self) -> None:
        from kernel.period import fiscal_quarter
        from datetime import date
        assert fiscal_quarter(date(2026, 4, 1)) == 2
        assert fiscal_quarter(date(2026, 6, 30)) == 2

    def test_fiscal_quarter_q3(self) -> None:
        from kernel.period import fiscal_quarter
        from datetime import date
        assert fiscal_quarter(date(2026, 7, 1)) == 3
        assert fiscal_quarter(date(2026, 9, 30)) == 3

    def test_fiscal_quarter_q4(self) -> None:
        from kernel.period import fiscal_quarter
        from datetime import date
        assert fiscal_quarter(date(2026, 10, 1)) == 4
        assert fiscal_quarter(date(2026, 12, 31)) == 4

    def test_date_range_inclusive(self) -> None:
        from kernel.period import date_range
        from datetime import date
        dates = list(date_range(date(2026, 1, 1), date(2026, 1, 3)))
        assert len(dates) == 3
        assert dates[0] == date(2026, 1, 1)
        assert dates[-1] == date(2026, 1, 3)

    def test_date_range_single_day(self) -> None:
        from kernel.period import date_range
        from datetime import date
        dates = list(date_range(date(2026, 6, 15), date(2026, 6, 15)))
        assert len(dates) == 1

    def test_date_range_empty(self) -> None:
        from kernel.period import date_range
        from datetime import date
        dates = list(date_range(date(2026, 1, 5), date(2026, 1, 1)))
        assert dates == []
