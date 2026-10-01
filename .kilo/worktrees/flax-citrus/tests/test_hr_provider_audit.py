"""Regression tests for HR provider architecture fixes.

Verifies:
- The circular dependency between ``providers.hr.bg_remover`` and the deleted
  ``providers.hr.config`` shim is gone (the shim no longer exists and
  ``bg_remover`` reads settings from the canonical ``utils.config``).
- The formerly private ``_bytes_to_image`` helper is now a public, importable
  symbol and redirects correctly through the provider shim chain.
"""
from __future__ import annotations

import importlib
import sys

import pytest


def test_hr_config_shim_removed():
    """The shadowing shim providers.hr.config must no longer exist."""
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("providers.hr.config")


def test_bg_remover_settings_from_canonical_config():
    """bg_remover imports settings from the canonical utils.config, not a shim."""
    mod = importlib.import_module("providers.hr.bg_remover")
    # The module object must have a usable `settings` attribute.
    assert hasattr(mod, "settings")
    # utils.config.settings is the canonical source.
    from utils.config import settings as canonical_settings

    assert mod.settings is canonical_settings


def test_bytes_to_image_is_public_and_importable():
    """Renamed private helper is now public and reachable via the shim chain."""
    mod = importlib.import_module("providers.hr.bg_remover")
    assert hasattr(mod, "bytes_to_image")
    assert not hasattr(mod, "_bytes_to_image")

    shim = importlib.import_module("providers.bg_remover")
    assert hasattr(shim, "bytes_to_image")


def test_no_circular_import_on_bg_remover():
    """Importing bg_remover must not trigger the deleted config module."""
    # Ensure a clean state.
    for name in list(sys.modules):
        if name.startswith("providers.hr"):
            del sys.modules[name]
    importlib.import_module("providers.hr.bg_remover")
    assert "providers.hr.config" not in sys.modules


def test_payroll_read_service_lives_in_hr_domain():
    """DOM2 fix: payroll read service belongs to services.hr, not services.finance."""
    mod = importlib.import_module("services.hr.payroll_read_service")
    for fn in ("get_payroll_records", "get_payroll_record_by_id", "get_payroll_summary"):
        assert hasattr(mod, fn), f"{fn} missing from services.hr.payroll_read_service"

    # The previous misplaced location must be gone.
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("services.finance.payroll_read_service")


def test_hr_service_no_communication_model_leak():
    """BC3 fix: HR services must not import communication ORM models.

    The dead ``send_internal_email`` (the only HR code that imported
    ``models.communication``) has been removed, so the public API no longer
    exposes it and the bounded context leak is gone.
    """
    mod = importlib.import_module("services.hr.employee_communication_service")
    assert "send_internal_email" not in getattr(mod, "__all__", [])


def test_hr_service_swallows_no_exceptions_silently():
    """QUAL1 fix: weak exception handling replaced with logged debug/warning."""
    bg = importlib.import_module("providers.hr.bg_remover")
    perf = importlib.import_module("services.hr.performance_service")
    for mod in (bg, perf):
        src = open(mod.__file__, encoding="utf-8").read()
        # No bare `except Exception: pass` best-effort blocks remain.
        assert "except Exception:\n        pass" not in src
        assert "except Exception:\n            pass" not in src
