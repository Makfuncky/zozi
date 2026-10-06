"""Paired tests for geography provider fixes.

Verifies the exact items repaired in E-05:
  * HAS_GEO / HAS_GEOIP flags are bool and exposed on the geo module.
  * CountryDetectionProvider.health_check() returns a dict with status/provider.
  * _lookup_geoip2 does not raise ModuleNotFoundError when geoip2 is absent
    and the cached reader is None.
  * HAS_GEO gates detect_country_from_ip degradation path.
"""
from __future__ import annotations

import importlib
from unittest.mock import MagicMock, patch

import pytest


class TestGeoFlags:
    """Flags are present, boolean, and import-safe."""

    def test_has_geo_is_bool(self):
        from providers.geography import geo as geo_mod

        assert hasattr(geo_mod, "HAS_GEO")
        assert isinstance(geo_mod.HAS_GEO, bool)

    def test_has_geoip_alias_exists_and_is_bool(self):
        from providers.geography import geo as geo_mod

        assert hasattr(geo_mod, "HAS_GEOIP")
        assert isinstance(geo_mod.HAS_GEOIP, bool)

    def test_geoip_module_has_geoip_flag(self):
        from providers.geography import geoip as geoip_mod

        assert hasattr(geoip_mod, "HAS_GEOIP")
        assert isinstance(geoip_mod.HAS_GEOIP, bool)


class TestHealthCheck:
    """Law 129: CountryDetectionProvider exposes health_check()."""

    def setup_method(self):
        from providers.geography.geo import CountryDetectionProvider

        self.provider = CountryDetectionProvider()

    def test_health_check_returns_dict(self):
        result = self.provider.health_check()
        assert isinstance(result, dict)

    def test_health_check_contains_status(self):
        result = self.provider.health_check()
        assert "status" in result

    def test_health_check_contains_provider(self):
        result = self.provider.health_check()
        assert result.get("provider") == "CountryDetectionProvider"

    def test_health_check_contains_geo_available(self):
        result = self.provider.health_check()
        assert "geo_available" in result


class TestGeoip2MissingSdk:
    """_lookup_geoip2 must not raise when geoip2 is missing."""

    def setup_method(self):
        from providers.geography.geo import CountryDetectionProvider

        self.provider = CountryDetectionProvider()

    def test_lookup_geoip2_no_sdk_returns_none(self):
        self.provider._geoip_reader = None
        fake_builtins = MagicMock()
        fake_builtins.__import__ = MagicMock(
            side_effect=lambda name, *args, **kwargs: (_ for _ in ()).throw(ModuleNotFoundError(name))
        )
        with patch.dict("sys.modules", {"geoip2": None, "geoip2.database": None}):
            with patch("builtins.__import__", side_effect=ModuleNotFoundError("No module named 'geoip2'")):
                result = self.provider._lookup_geoip2("1.2.3.4")
        assert result is None

    def test_lookup_geoip2_no_sdk_with_cached_reader(self):
        mock_reader = MagicMock()
        mock_response = MagicMock()
        mock_response.country.iso_code = "DE"
        mock_reader.country.return_value = mock_response
        self.provider._geoip_reader = mock_reader

        result = self.provider._lookup_geoip2("1.2.3.4")
        assert result == "DE"


class TestHasGeoDegradation:
    """HAS_GEO gates country detection degradation path."""

    def setup_method(self):
        from providers.geography.geo import CountryDetectionProvider

        self.provider = CountryDetectionProvider()

    def test_detect_country_from_ip_returns_default_when_disabled(self):
        from providers.geography import geo as geo_mod

        original = geo_mod.HAS_GEO
        try:
            geo_mod.HAS_GEO = False
            code, source = self.provider.detect_country_from_ip({}, "1.2.3.4")
            assert code == "US"
            assert source == "disabled"
        finally:
            geo_mod.HAS_GEO = original
