"""Regression test for the analytics provider.

Covers the ``AnalyticsProvider`` instantiation bug where
``_AnalyticsProviderSettings.analytics_default_period_days`` was referenced but
never defined (AttributeError on ``AnalyticsProvider()``).

The provider module is loaded directly via importlib so the test does not trip
the unrelated circular-import in ``providers.ai.text`` exposed by
``providers/__init__.py``.
"""
from __future__ import annotations

import importlib.util
import os
import sys

import pytest


def _load_provider_module():
    backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    backend_dir = os.path.join(backend_root, "backend")
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)
    path = os.path.join(backend_dir, "providers", "analytics", "analytics.py")
    spec = importlib.util.spec_from_file_location("isolated_analytics_provider_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_analytics_provider_instantiates():
    module = _load_provider_module()
    provider = module.AnalyticsProvider()
    assert provider._default_period_days == 30


def test_dashboard_summary_period_mapping():
    module = _load_provider_module()
    provider = module.AnalyticsProvider()
    for period, expected_days in [("7d", 7), ("30d", 30), ("90d", 90), ("1y", 365)]:
        summary = provider._get_dashboard_summary(country_code="OMR", period=period)
        assert summary["days"] == expected_days
        assert summary["period"] == period
        assert summary["country_code"] == "OMR"


def test_dashboard_summary_falls_back_to_default_period():
    module = _load_provider_module()
    provider = module.AnalyticsProvider()
    summary = provider._get_dashboard_summary(period="bogus")
    assert summary["days"] == 30
