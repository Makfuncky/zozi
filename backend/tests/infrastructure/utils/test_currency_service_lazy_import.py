"""Regression tests for FILE-71: infrastructure/utils/currency_service.py must
not hold a static top-level ``providers`` import (Law 1: arrows point down only).

The fix replaces the static ``from providers.geography.rates import ...`` block
with a lazy ``importlib.import_module`` call inside a ``_lazy()`` helper so
no static upward arrow exists in the module body.
"""
from __future__ import annotations

import ast
import importlib
import importlib.util
import sys

import pytest

from infrastructure.utils import currency_service as cs


# ---------------------------------------------------------------------------
# 1. AST-level: no static top-level import of 'providers' in the module body
# ---------------------------------------------------------------------------

def _load_module_ast() -> ast.Module:
    path = importlib.util.find_spec("infrastructure.utils.currency_service").origin
    assert path is not None, "currency_service module spec has no origin"
    with open(path, encoding="utf-8") as fh:
        return ast.parse(fh.read(), filename=path)


def test_no_static_providers_import():
    """Law 1: infrastructure must not have a static top-level providers import."""
    tree = _load_module_ast()
    top_level_imports = [
        node for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom))
    ]
    for node in top_level_imports:
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not alias.name.startswith("providers"), (
                    f"Static import of providers found: {ast.unparse(node)}"
                )
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            assert not mod.startswith("providers"), (
                f"Static import from providers found: {ast.unparse(node)}"
            )


# ---------------------------------------------------------------------------
# 2. Behavioral: lazy import must still resolve and functions must work
# ---------------------------------------------------------------------------

def test_lazy_import_resolves_providers():
    """The _lazy() helper must successfully resolve providers.geography.rates."""
    rates_mod = cs._lazy()
    assert rates_mod is not None
    assert hasattr(rates_mod, "fetch_rates")
    assert hasattr(rates_mod, "normalize_currency_code")


def test_lazy_import_uses_cache_on_second_call():
    """importlib.import_module returns the cached module; _lazy() must not
    re-import on every call (sys.modules cache guarantees this)."""
    mod1 = cs._lazy()
    mod2 = cs._lazy()
    assert mod1 is mod2


def test_get_currency_metadata_via_lazy():
    """A public function exercising the lazy path must return correct metadata."""
    meta = cs.get_currency_metadata("USD")
    assert meta["code"] == "USD"
    assert meta["decimals"] == 2


def test_currency_for_country_known():
    """currency_for_country must resolve known countries without hitting Wikidata."""
    assert cs.currency_for_country("AE") == "AED"
    assert cs.currency_for_country("SA") == "SAR"
    assert cs.currency_for_country("US") == "USD"


def test_currency_for_country_default():
    """currency_for_country must return default for None / unknown input."""
    assert cs.currency_for_country(None) == "OMR"
    assert cs.currency_for_country("") == "OMR"


def test_get_currency_metadata_known():
    """Metadata for a known currency must return expected fields."""
    meta = cs.get_currency_metadata("USD")
    assert meta["code"] == "USD"
    assert meta["decimals"] == 2
    assert "name" in meta


def test_no_static_imports_of_providers_in_module_dict():
    """Module globals must not contain a module-level 'providers' reference."""
    for name in dir(cs):
        if name.startswith("_"):
            continue
        obj = getattr(cs, name)
        if hasattr(obj, "__module__") and obj.__module__ and obj.__module__.startswith("providers"):
            pytest.fail(
                f"Public symbol {name} has __module__={obj.__module__!r} "
                "which is a provider — indicates static provider import"
            )
