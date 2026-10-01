"""Regression test for the `data` circuit-exempt facade and clean app boot.

These tests guard the reorg-era fix where the `data` package is the sanctioned
bridge that `routers`/`controllers` use to reach `models`/`services` without
importing those layers directly (the architecture audit forbids upward calls).

Run from repo root with the backend venv, e.g.:
    & "backend/venv/Scripts/python.exe" -m pytest tests/test_data_facade_boot.py -q
"""
from __future__ import annotations

import os
import sys
import types

import pytest

BACKEND = os.path.join(os.path.dirname(__file__), "..", "backend")
BACKEND = os.path.abspath(BACKEND)

if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only")
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("CSRF_DISABLED", "true")


def test_models_facade_resolves_classes():
    """`data.models` must expose ORM classes that live in model submodules
    whose ``__all__`` does not re-export them (e.g. PayrollRecord, Budget)."""
    from data.models import PayrollRecord, Budget  # noqa: F401

    assert PayrollRecord is not None
    assert Budget is not None


def test_services_facade_forwards_submodules():
    """`data.services` must forward submodule names used by routers."""
    from data.services import finance_automation  # noqa: F401
    from data.services import erp_finance_service  # noqa: F401
    from data.services import trading_service  # noqa: F401
    from data.services import import_service  # noqa: F401
    from data.services import automation_scheduler  # noqa: F401

    assert finance_automation is not None


def test_facade_backed_routers_import():
    """Routers that depend on the `data` facade must import cleanly."""
    import importlib

    for name in (
        "finance_automation",
        "finance_erp",
        "hierarchy",
        "trading",
        "imports",
        "automation",
    ):
        mod = importlib.import_module(f"routers.{name}")
        assert isinstance(mod, types.ModuleType)


def test_app_boots_without_router_failures(caplog):
    """`import main` must succeed and load every router with zero failures."""
    import logging

    with caplog.at_level(logging.ERROR, logger="main"):
        import main  # noqa: F401

    failures = [
        r.getMessage()
        for r in caplog.records
        if "Failed to load" in r.getMessage()
    ]
    assert failures == [], f"router load failures: {failures}"
    assert hasattr(main, "app")
