"""Comprehensive tests for geography/ provider subpackage.

Tests cover:
- backend/providers/geography/ (country.py, country_http.py, external_data.py,
  geo.py, geoip.py, ip.py, map.py, rates.py)

Run with: pytest tests/providers/test_geography_providers.py -v
"""

from __future__ import annotations

import asyncio
import ipaddress
import json
import sys
import os
from decimal import Decimal
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, Mock, patch, mock_open

import pytest

# Ensure backend is on the path for imports
BACKEND = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)


# ===========================================================================
# geography/country.py — CountrySearchProvider
# ===========================================================================


class TestCountrySearchProvider:
    """Tests for backend/providers/geography/country.py::CountrySearchProvider."""

    def setup_method(self):
        from providers.geography.country import CountrySearchProvider

        self.provider = CountrySearchProvider()

    def test_init_default_country(self):
        assert self.provider._default_country == "US"

    def test_init_cache_empty(self):
        assert self.provider._country_cache == {}

    def test_search_country_by_name(self):
        results = self.provider.search_country("Germany")
        assert len(results) == 1
        assert results[0]["code"] == "DE"

    def test_search_country_by_code(self):
        results = self.provider.search_country("US")
        assert len(results) >= 1
        assert any(c["code"] == "US" for c in results)

    def test_search_country_by_region(self):
        results = self.provider.search_country("Europe")
        assert len(results) >= 4

    def test_search_country_by_capital(self):
        results = self.provider.search_country("Berlin")
        assert any(c["code"] == "DE" for c in results)

    def test_search_country_case_insensitive(self):
        results = self.provider.search_country("gErMaNy")
        assert len(results) == 1
        assert results[0]["code"] == "DE"

    def test_search_country_whitespace_trimmed(self):
        results = self.provider.search_country("  Japan  ")
        assert len(results) == 1
        assert results[0]["code"] == "JP"

    def test_search_country_no_match(self):
        results = self.provider.search_country("NonExistentLand")
        assert results == []

    def test_search_country_max_20_results(self):
        results = self.provider.search_country("")
        assert len(results) <= 20

    def test_get_country_details_known(self):
        details = self.provider.get_country_details("US")
        assert details["code"] == "US"
        assert details["name"] == "United States"
        assert details["region"] == "Americas"

    def test_get_country_details_unknown(self):
        details = self.provider.get_country_details("ZZ")
        assert details["code"] == "ZZ"
        assert details["region"] == "Unknown"

    def test_get_country_details_uppercase_input(self):
        details = self.provider.get_country_details("us")
        assert details["code"] == "US"

    def test_get_country_details_cached(self):
        self.provider.get_country_details("DE")
        assert "DE" in self.provider._country_cache
        details = self.provider.get_country_details("DE")
        assert details["name"] == "Germany"

    def test_get_country_by_name_found(self):
        result = self.provider.get_country_by_name("France")
        assert result is not None
        assert result["code"] == "FR"

    def test_get_country_by_name_not_found(self):
        result = self.provider.get_country_by_name("Atlantis")
        assert result is None

    def test_get_countries_by_region(self):
        countries = self.provider.get_countries_by_region("Africa")
        assert len(countries) >= 3

    def test_get_countries_by_region_no_match(self):
        countries = self.provider.get_countries_by_region("Antarctica")
        assert countries == []

    def test_get_currencies(self):
        currencies = self.provider.get_currencies()
        assert "USD" in currencies
        assert "EUR" in currencies
        assert "US" in currencies["USD"]

    def test_get_known_countries_returns_20(self):
        countries = self.provider._get_known_countries()
        assert len(countries) == 20


# ===========================================================================
# geography/country_http.py — Async HTTP helpers
# ===========================================================================


class TestCountryHttp:
    """Tests for backend/providers/geography/country_http.py."""

    def test_default_timeout(self):
        from providers.geography.country_http import DEFAULT_TIMEOUT

        assert DEFAULT_TIMEOUT == 10.0

    def test_country_http_error_is_exception(self):
        from providers.geography.country_http import CountryHttpError

        assert issubclass(CountryHttpError, Exception)

    @pytest.mark.asyncio
    async def test_get_json_success(self):
        from providers.geography.country_http import get_json

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"name": "Test"}

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("providers.geography.country_http.httpx.AsyncClient", return_value=mock_client):
            result = await get_json("https://example.com/api")
            assert result == {"name": "Test"}

    @pytest.mark.asyncio
    async def test_get_json_non_200_returns_none(self):
        from providers.geography.country_http import get_json

        mock_response = MagicMock()
        mock_response.status_code = 404

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("providers.geography.country_http.httpx.AsyncClient", return_value=mock_client):
            result = await get_json("https://example.com/api")
            assert result is None

    @pytest.mark.asyncio
    async def test_get_json_request_error_raises(self):
        from providers.geography.country_http import get_json, CountryHttpError

        import httpx

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(side_effect=httpx.RequestError("connection refused"))

        with patch("providers.geography.country_http.httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(CountryHttpError):
                await get_json("https://example.com/api")

    @pytest.mark.asyncio
    async def test_get_json_decode_failure_returns_none(self):
        from providers.geography.country_http import get_json

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("err", "", 0)

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("providers.geography.country_http.httpx.AsyncClient", return_value=mock_client):
            result = await get_json("https://example.com/api")
            assert result is None

    @pytest.mark.asyncio
    async def test_fetch_restcountries_raw_empty_term(self):
        from providers.geography.country_http import fetch_restcountries_raw

        result = await fetch_restcountries_raw("")
        assert result is None

    @pytest.mark.asyncio
    async def test_fetch_restcountries_raw_two_letter_code(self):
        from providers.geography.country_http import fetch_restcountries_raw

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"name": {"common": "Germany"}}]

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("providers.geography.country_http.httpx.AsyncClient", return_value=mock_client):
            result = await fetch_restcountries_raw("DE")
            assert result == [{"name": {"common": "Germany"}}]

    @pytest.mark.asyncio
    async def test_fetch_restcountries_raw_three_letter_code(self):
        from providers.geography.country_http import fetch_restcountries_raw

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"name": {"common": "Germany"}}]

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("providers.geography.country_http.httpx.AsyncClient", return_value=mock_client):
            result = await fetch_restcountries_raw("DEU")
            assert result is not None

    @pytest.mark.asyncio
    async def test_fetch_restcountries_raw_full_name(self):
        from providers.geography.country_http import fetch_restcountries_raw

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"name": {"common": "Germany"}}]

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("providers.geography.country_http.httpx.AsyncClient", return_value=mock_client):
            result = await fetch_restcountries_raw("Germany")
            assert result is not None

    @pytest.mark.asyncio
    async def test_fetch_worldbank_indicator_raw(self):
        from providers.geography.country_http import fetch_worldbank_indicator_raw

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{}, [{"value": 100}]]

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("providers.geography.country_http.httpx.AsyncClient", return_value=mock_client):
            result = await fetch_worldbank_indicator_raw("US", "NY.GDP.MKTP.CD")
            assert result is not None

    @pytest.mark.asyncio
    async def test_fetch_geodb_cities_raw(self):
        from providers.geography.country_http import fetch_geodb_cities_raw

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"cities": ["Berlin"]}

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("providers.geography.country_http.httpx.AsyncClient", return_value=mock_client):
            result = await fetch_geodb_cities_raw("DE")
            assert result is not None

    @pytest.mark.asyncio
    async def test_fetch_nager_holidays_raw_mapped_code(self):
        from providers.geography.country_http import fetch_nager_holidays_raw

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"date": "2024-01-01"}]

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("providers.geography.country_http.httpx.AsyncClient", return_value=mock_client):
            result = await fetch_nager_holidays_raw("GB", 2024)
            assert result is not None

    @pytest.mark.asyncio
    async def test_fetch_nager_holidays_raw_unmapped_code(self):
        from providers.geography.country_http import fetch_nager_holidays_raw

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("providers.geography.country_http.httpx.AsyncClient", return_value=mock_client):
            result = await fetch_nager_holidays_raw("FR", 2024)
            assert result is not None

    @pytest.mark.asyncio
    async def test_fetch_vat_rate_raw(self):
        from providers.geography.country_http import fetch_vat_rate_raw

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"standard_rate": 20}

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("providers.geography.country_http.httpx.AsyncClient", return_value=mock_client):
            result = await fetch_vat_rate_raw("DE")
            assert result is not None


# ===========================================================================
# geography/external_data.py — aiohttp-based external data fetchers
# ===========================================================================


class TestExternalData:
    """Tests for backend/providers/geography/external_data.py."""

    def test_url_constants(self):
        from providers.geography.external_data import (
            REST_COUNTRIES_URL,
            WORLD_BANK_URL,
            GEODB_CITIES_URL,
            NAGER_DATE_URL,
        )

        assert "{country_code}" in REST_COUNTRIES_URL
        assert "{country_code}" in WORLD_BANK_URL
        assert "{country_code}" in GEODB_CITIES_URL
        assert "{year}" in NAGER_DATE_URL
        assert "{country_code}" in NAGER_DATE_URL

    @pytest.mark.asyncio
    async def test_fetch_restcountries_success(self):
        from providers.geography.external_data import fetch_restcountries

        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value=[{"name": "Germany"}])

        mock_session = AsyncMock()
        mock_session.get = MagicMock()
        mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_session.get.return_value.__aexit__ = AsyncMock(return_value=None)

        result = await fetch_restcountries(mock_session, "DE")
        assert result == {"name": "Germany"}

    @pytest.mark.asyncio
    async def test_fetch_restcountries_non_200(self):
        from providers.geography.external_data import fetch_restcountries

        mock_resp = AsyncMock()
        mock_resp.status = 404

        mock_session = AsyncMock()
        mock_session.get = MagicMock()
        mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_session.get.return_value.__aexit__ = AsyncMock(return_value=None)

        result = await fetch_restcountries(mock_session, "DE")
        assert result == {}

    @pytest.mark.asyncio
    async def test_fetch_restcountries_empty_list(self):
        from providers.geography.external_data import fetch_restcountries

        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value=[])

        mock_session = AsyncMock()
        mock_session.get = MagicMock()
        mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_session.get.return_value.__aexit__ = AsyncMock(return_value=None)

        result = await fetch_restcountries(mock_session, "DE")
        assert result == {}

    @pytest.mark.asyncio
    async def test_fetch_worldbank_success(self):
        from providers.geography.external_data import fetch_worldbank

        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value = [{}, [{"indicator": "GDP"}]])

        mock_session = AsyncMock()
        mock_session.get = MagicMock()
        mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_session.get.return_value.__aexit__ = AsyncMock(return_value=None)

        result = await fetch_worldbank(mock_session, "US")
        assert result == [{"indicator": "GDP"}]

    @pytest.mark.asyncio
    async def test_fetch_worldbank_non_200(self):
        from providers.geography.external_data import fetch_worldbank

        mock_resp = AsyncMock()
        mock_resp.status = 500

        mock_session = AsyncMock()
        mock_session.get = MagicMock()
        mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_session.get.return_value.__aexit__ = AsyncMock(return_value=None)

        result = await fetch_worldbank(mock_session, "US")
        assert result == {}

    @pytest.mark.asyncio
    async def test_fetch_worldbank_list_too_short(self):
        from providers.geography.external_data import fetch_worldbank

        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value=[{}])

        mock_session = AsyncMock()
        mock_session.get = MagicMock()
        mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_session.get.return_value.__aexit__ = AsyncMock(return_value=None)

        result = await fetch_worldbank(mock_session, "US")
        assert result == {}

    @pytest.mark.asyncio
    async def test_fetch_geodb_cities_success(self):
        from providers.geography.external_data import fetch_geodb_cities

        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"data": ["Berlin", "Munich"]})

        mock_session = AsyncMock()
        mock_session.get = MagicMock()
        mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_session.get.return_value.__aexit__ = AsyncMock(return_value=None)

        result = await fetch_geodb_cities(mock_session, "DE")
        assert result == ["Berlin", "Munich"]

    @pytest.mark.asyncio
    async def test_fetch_geodb_cities_non_200(self):
        from providers.geography.external_data import fetch_geodb_cities

        mock_resp = AsyncMock()
        mock_resp.status = 403

        mock_session = AsyncMock()
        mock_session.get = MagicMock()
        mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_session.get.return_value.__aexit__ = AsyncMock(return_value=None)

        result = await fetch_geodb_cities(mock_session, "DE")
        assert result == []

    @pytest.mark.asyncio
    async def test_fetch_nager_holidays_success(self):
        from providers.geography.external_data import fetch_nager_holidays

        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value=[{"date": "2024-01-01", "name": "New Year"}])

        mock_session = AsyncMock()
        mock_session.get = MagicMock()
        mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_session.get.return_value.__aexit__ = AsyncMock(return_value=None)

        result = await fetch_nager_holidays(mock_session, "US", 2024)
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_fetch_nager_holidays_non_200(self):
        from providers.geography.external_data import fetch_nager_holidays

        mock_resp = AsyncMock()
        mock_resp.status = 404

        mock_session = AsyncMock()
        mock_session.get = MagicMock()
        mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_session.get.return_value.__aexit__ = AsyncMock(return_value=None)

        result = await fetch_nager_holidays(mock_session, "US", 2024)
        assert result == []


# ===========================================================================
# geography/geo.py — CountryDetectionProvider, IpLocation, resolve_ip_location
# ===========================================================================


class TestCountryDetectionProvider:
    """Tests for backend/providers/geography/geo.py::CountryDetectionProvider."""

    def setup_method(self):
        from providers.geography.geo import CountryDetectionProvider

        self.provider = CountryDetectionProvider()

    def test_init(self):
        assert self.provider._geoip_reader is None
        assert self.provider._default_country == "US"

    def test_ip_header_mapping_exists(self):
        from providers.geography.geo import CountryDetectionProvider

        assert "X-Forwarded-For" in CountryDetectionProvider.IP_HEADER_MAPPING
        assert "X-Real-IP" in CountryDetectionProvider.IP_HEADER_MAPPING
        assert "CF-Connecting-IP" in CountryDetectionProvider.IP_HEADER_MAPPING

    def test_detect_country_from_ip_no_headers(self):
        code, source = self.provider.detect_country_from_ip({}, None)
        assert code == "US"
        assert source == "unknown"

    def test_detect_country_from_ip_private(self):
        code, source = self.provider.detect_country_from_ip({}, "192.168.1.1")
        assert code == "US"
        assert source == "private"

    def test_detect_country_from_ip_loopback(self):
        code, source = self.provider.detect_country_from_ip({}, "127.0.0.1")
        assert code == "US"
        assert source == "private"

    def test_detect_country_from_ip_link_local(self):
        code, source = self.provider.detect_country_from_ip({}, "169.254.1.1")
        assert code == "US"
        assert source == "private"

    def test_detect_country_from_ip_x_forwarded_for(self):
        with patch.object(self.provider, "_lookup_country_by_ip", return_value=("DE", "geoip2")):
            code, source = self.provider.detect_country_from_ip(
                {"X-Forwarded-For": "85.214.132.117, 70.41.3.18"}, None
            )
            assert code == "DE"
            assert source == "geoip2"

    def test_detect_country_from_ip_x_real_ip(self):
        with patch.object(self.provider, "_lookup_country_by_ip", return_value=("FR", "ipapi")):
            code, source = self.provider.detect_country_from_ip(
                {"X-Real-IP": "178.32.100.1"}, None
            )
            assert code == "FR"
            assert source == "ipapi"

    def test_detect_country_from_ip_cf_connecting_ip(self):
        with patch.object(self.provider, "_lookup_country_by_ip", return_value=("JP", "geoip2")):
            code, source = self.provider.detect_country_from_ip(
                {"CF-Connecting-IP": "103.21.244.0"}, None
            )
            assert code == "JP"

    def test_extract_ip_x_forwarded_for(self):
        ip = self.provider._extract_ip({"X-Forwarded-For": "1.2.3.4, 5.6.7.8"}, None)
        assert ip == "1.2.3.4"

    def test_extract_ip_x_real_ip(self):
        ip = self.provider._extract_ip({"X-Real-IP": "1.2.3.4"}, None)
        assert ip == "1.2.3.4"

    def test_extract_ip_fallback_to_client_host(self):
        ip = self.provider._extract_ip({}, "1.2.3.4")
        assert ip == "1.2.3.4"

    def test_extract_ip_no_match(self):
        ip = self.provider._extract_ip({}, None)
        assert ip is None

    def test_is_private_ip_private(self):
        assert self.provider._is_private_ip("192.168.1.1") is True

    def test_is_private_ip_loopback(self):
        assert self.provider._is_private_ip("127.0.0.1") is True

    def test_is_private_ip_public(self):
        assert self.provider._is_private_ip("8.8.8.8") is False

    def test_is_private_ip_invalid(self):
        assert self.provider._is_private_ip("not-an-ip") is False

    def test_is_private_ip_link_local(self):
        assert self.provider._is_private_ip("169.254.0.1") is True

    def test_lookup_country_by_ip_geoip2_success(self):
        with patch.object(self.provider, "_lookup_geoip2", return_value="DE"):
            country, source = self.provider._lookup_country_by_ip("85.214.132.117")
            assert country == "DE"
            assert source == "geoip2"

    def test_lookup_country_by_ip_fallback_to_ipapi(self):
        with patch.object(self.provider, "_lookup_geoip2", return_value=None), \
             patch.object(self.provider, "_lookup_ipapi", return_value="FR"):
            country, source = self.provider._lookup_country_by_ip("178.32.100.1")
            assert country == "FR"
            assert source == "ipapi"

    def test_lookup_country_by_ip_default(self):
        with patch.object(self.provider, "_lookup_geoip2", return_value=None), \
             patch.object(self.provider, "_lookup_ipapi", return_value=None):
            country, source = self.provider._lookup_country_by_ip("1.2.3.4")
            assert country == "US"
            assert source == "default"

    def test_lookup_geoip2_no_db(self):
        with patch("geoip2.database.Reader", side_effect=Exception("no db")):
            result = self.provider._lookup_geoip2("8.8.8.8")
            assert result is None

    def test_lookup_geoip2_success(self):
        mock_reader = MagicMock()
        mock_response = MagicMock()
        mock_response.country.iso_code = "DE"
        mock_reader.country.return_value = mock_response

        with patch("geoip2.database.Reader", return_value=mock_reader):
            self.provider._geoip_reader = None
            result = self.provider._lookup_geoip2("85.214.132.117")
            assert result == "DE"

    def test_lookup_geoip2_cached_reader(self):
        mock_reader = MagicMock()
        mock_response = MagicMock()
        mock_response.country.iso_code = "FR"
        mock_reader.country.return_value = mock_response

        self.provider._geoip_reader = mock_reader
        result = self.provider._lookup_geoip2("178.32.100.1")
        assert result == "FR"

    def test_lookup_geoip2_no_iso_code(self):
        mock_reader = MagicMock()
        mock_response = MagicMock()
        mock_response.country.iso_code = None
        mock_reader.country.return_value = mock_response

        self.provider._geoip_reader = mock_reader
        result = self.provider._lookup_geoip2("1.2.3.4")
        assert result is None

    def test_lookup_ipapi_success(self):
        mock_resp = MagicMock()
        mock_resp.read.return_value = b'{"country_code": "DE", "country": "Germany"}'
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=None)

        with patch("providers.geography.geo.urllib.request.urlopen", return_value=mock_resp):
            with patch("providers.geography.geo.urllib.request.Request") as mock_req:
                mock_req.return_value = MagicMock()
                result = self.provider._lookup_ipapi("85.214.132.117")
                assert result == "DE"

    def test_lookup_ipapi_failure(self):
        with patch(
            "providers.geography.geo.urllib.request.urlopen",
            side_effect=Exception("timeout"),
        ):
            result = self.provider._lookup_ipapi("1.2.3.4")
            assert result is None

    def test_get_country_by_coordinates(self):
        result = self.provider.get_country_by_coordinates(52.52, 13.405)
        assert result == "US"

    def test_get_country_details(self):
        details = self.provider.get_country_details("DE")
        assert details["code"] == "DE"
        assert details["currency"] == "USD"


class TestIpLocation:
    """Tests for backend/providers/geography/geo.py::IpLocation dataclass."""

    def test_to_dict(self):
        from providers.geography.geo import IpLocation

        loc = IpLocation(
            ip="1.2.3.4",
            country="Germany",
            country_code="DE",
            region="Berlin",
            city="Berlin",
            latitude=52.52,
            longitude=13.405,
            isp="ISP",
            source="ipwho.is",
        )
        d = loc.to_dict()
        assert d["ip"] == "1.2.3.4"
        assert d["country_code"] == "DE"
        assert d["has_coordinates"] is True

    def test_to_dict_no_coordinates(self):
        from providers.geography.geo import IpLocation

        loc = IpLocation(ip="1.2.3.4")
        d = loc.to_dict()
        assert d["has_coordinates"] is False


class TestReverseLocation:
    """Tests for backend/providers/geography/geo.py::ReverseLocation dataclass."""

    def test_to_dict(self):
        from providers.geography.geo import ReverseLocation

        loc = ReverseLocation(
            latitude=52.52,
            longitude=13.405,
            display_name="Berlin, Germany",
            address={"city": "Berlin"},
            source="nominatim",
        )
        d = loc.to_dict()
        assert d["latitude"] == 52.52
        assert d["display_name"] == "Berlin, Germany"
        assert d["address"] == {"city": "Berlin"}

    def test_to_dict_default_address(self):
        from providers.geography.geo import ReverseLocation

        loc = ReverseLocation(latitude=0.0, longitude=0.0)
        d = loc.to_dict()
        assert d["address"] == {}


class TestResolveIpLocation:
    """Tests for backend/providers/geography/geo.py::resolve_ip_location."""

    def setup_method(self):
        from providers.geography.geo import _cache

        _cache._store.clear()

    def test_resolve_ip_location_private_ip_raises(self):
        from providers.geography.geo import resolve_ip_location

        with pytest.raises(RuntimeError, match="private/local"):
            resolve_ip_location(ip="192.168.1.1")

    def test_resolve_ip_location_loopback_raises(self):
        from providers.geography.geo import resolve_ip_location

        with pytest.raises(RuntimeError, match="private/local"):
            resolve_ip_location(ip="127.0.0.1")

    def test_resolve_ip_location_localhost_raises(self):
        from providers.geography.geo import resolve_ip_location

        with pytest.raises(RuntimeError, match="private/local"):
            resolve_ip_location(ip="localhost")

    def test_resolve_ip_location_10_range_raises(self):
        from providers.geography.geo import resolve_ip_location

        with pytest.raises(RuntimeError, match="private/local"):
            resolve_ip_location(ip="10.0.0.1")

    def test_resolve_ip_location_192_168_raises(self):
        from providers.geography.geo import resolve_ip_location

        with pytest.raises(RuntimeError, match="private/local"):
            resolve_ip_location(ip="192.168.0.1")

    def test_resolve_ip_location_from_headers(self):
        from providers.geography.geo import resolve_ip_location

        with patch("providers.geography.geo.requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {
                "ip": "1.2.3.4",
                "success": True,
                "country": "Germany",
                "countryCode": "DE",
                "region": "Berlin",
                "city": "Berlin",
                "latitude": 52.52,
                "longitude": 13.405,
                "connection": {"isp": "ISP"},
            }
            mock_get.return_value = mock_resp

            result = resolve_ip_location(
                client_host="127.0.0.1",
                forwarded_for="1.2.3.4",
            )
            assert result.country_code == "DE"
            assert result.source == "ipwho.is"

    def test_resolve_ip_location_all_providers_fail(self):
        import requests as req_lib
        from providers.geography.geo import resolve_ip_location

        with patch("providers.geography.geo.requests.get", side_effect=req_lib.RequestException("network down")):
            with pytest.raises(RuntimeError, match="All location providers failed"):
                resolve_ip_location(ip="1.2.3.4")

    def test_resolve_ip_location_caching(self):
        import requests as req_lib
        from providers.geography.geo import resolve_ip_location

        with patch("providers.geography.geo.requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {
                "ip": "1.2.3.4",
                "success": True,
                "country": "Germany",
                "countryCode": "DE",
                "latitude": 52.52,
                "longitude": 13.405,
            }
            mock_get.return_value = mock_resp

            result1 = resolve_ip_location(ip="1.2.3.4")
            result2 = resolve_ip_location(ip="1.2.3.4")
            assert result1 == result2
            assert mock_get.call_count == 1

    def test_resolve_ip_location_bad_json(self):
        from providers.geography.geo import resolve_ip_location

        with patch("providers.geography.geo.requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.side_effect = json.JSONDecodeError("err", "", 0)
            mock_get.return_value = mock_resp

            with pytest.raises(RuntimeError, match="All location providers failed"):
                resolve_ip_location(ip="1.2.3.4")


class TestReverseGeocode:
    """Tests for backend/providers/geography/geo.py::reverse_geocode."""

    def setup_method(self):
        from providers.geography.geo import _cache

        _cache._store.clear()

    def test_reverse_geocode_success(self):
        from providers.geography.geo import reverse_geocode

        with patch("providers.geography.geo.requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {
                "display_name": "Berlin, Germany",
                "address": {"city": "Berlin", "country": "Germany"},
            }
            mock_get.return_value = mock_resp

            result = reverse_geocode(52.52, 13.405)
            assert result.display_name == "Berlin, Germany"
            assert result.source == "nominatim.openstreetmap.org"

    def test_reverse_geocode_non_200_raises(self):
        from providers.geography.geo import reverse_geocode

        with patch("providers.geography.geo.requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 503
            mock_get.return_value = mock_resp

            with pytest.raises(RuntimeError, match="Reverse geocode HTTP 503"):
                reverse_geocode(52.52, 13.405)

    def test_reverse_geocode_network_error_raises(self):
        import requests as req_lib
        from providers.geography.geo import reverse_geocode

        with patch(
            "providers.geography.geo.requests.get",
            side_effect=req_lib.RequestException("connection refused"),
        ):
            with pytest.raises(RuntimeError, match="Reverse geocode failed"):
                reverse_geocode(52.52, 13.405)

    def test_reverse_geocode_caching(self):
        from providers.geography.geo import reverse_geocode

        with patch("providers.geography.geo.requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"display_name": "Test"}
            mock_get.return_value = mock_resp

            result1 = reverse_geocode(52.52, 13.405)
            result2 = reverse_geocode(52.52, 13.405)
            assert result1 == result2
            assert mock_get.call_count == 1


class TestParseHelpers:
    """Tests for _parse_ipwhois, _parse_ipapi, _to_float, _client_ip_from_request."""

    def test_parse_ipwhois_success(self):
        from providers.geography.geo import _parse_ipwhois

        result = _parse_ipwhois({
            "ip": "1.2.3.4",
            "success": True,
            "country": "Germany",
            "countryCode": "DE",
            "region": "Berlin",
            "city": "Berlin",
            "latitude": 52.52,
            "longitude": 13.405,
            "connection": {"isp": "ISP"},
        })
        assert result is not None
        assert result.country_code == "DE"
        assert result.source == "ipwho.is"

    def test_parse_ipwhois_failure_flag(self):
        from providers.geography.geo import _parse_ipwhois

        result = _parse_ipwhois({"success": False})
        assert result is None

    def test_parse_ipwhois_malformed(self):
        from providers.geography.geo import _parse_ipwhois

        result = _parse_ipwhois({"success": True, "latitude": "not-a-number-but-ok"})
        assert result is not None

    def test_parse_ipapi_success(self):
        from providers.geography.geo import _parse_ipapi

        result = _parse_ipapi({
            "status": "success",
            "query": "1.2.3.4",
            "country": "Germany",
            "countryCode": "DE",
            "regionName": "Berlin",
            "city": "Berlin",
            "lat": 52.52,
            "lon": 13.405,
            "isp": "ISP",
        })
        assert result is not None
        assert result.country_code == "DE"
        assert result.source == "ip-api.com"

    def test_parse_ipapi_failure_status(self):
        from providers.geography.geo import _parse_ipapi

        result = _parse_ipapi({"status": "fail"})
        assert result is None

    def test_to_float_none(self):
        from providers.geography.geo import _to_float

        assert _to_float(None) is None

    def test_to_float_valid(self):
        from providers.geography.geo import _to_float

        assert _to_float("52.52") == 52.52

    def test_to_float_invalid(self):
        from providers.geography.geo import _to_float

        assert _to_float("abc") is None

    def test_client_ip_from_request_real_ip(self):
        from providers.geography.geo import _client_ip_from_request

        result = _client_ip_from_request("127.0.0.1", "1.2.3.4", "5.6.7.8")
        assert result == "5.6.7.8"

    def test_client_ip_from_request_forwarded_for(self):
        from providers.geography.geo import _client_ip_from_request

        result = _client_ip_from_request("127.0.0.1", "1.2.3.4, 9.9.9.9", None)
        assert result == "1.2.3.4"

    def test_client_ip_from_request_fallback(self):
        from providers.geography.geo import _client_ip_from_request

        result = _client_ip_from_request("127.0.0.1", None, None)
        assert result == "127.0.0.1"


class TestCache:
    """Tests for backend/providers/geography/geo.py::_Cache."""

    def test_cache_set_and_get(self):
        from providers.geography.geo import _Cache

        cache = _Cache(ttl=60)
        cache.set("key", "value")
        assert cache.get("key") == "value"

    def test_cache_miss(self):
        from providers.geography.geo import _Cache

        cache = _Cache(ttl=60)
        assert cache.get("nonexistent") is None

    def test_cache_expiry(self):
        from providers.geography.geo import _Cache

        cache = _Cache(ttl=0)
        cache.set("key", "value")
        import time

        time.sleep(0.01)
        assert cache.get("key") is None


# ===========================================================================
# geography/geoip.py — GeoIP lookups
# ===========================================================================


class TestGeoIP:
    """Tests for backend/providers/geography/geoip.py."""

    def test_constants(self):
        from providers.geography.geoip import GEOIP_CITY_DB, GEOIP_COUNTRY_DB

        assert GEOIP_CITY_DB == "data/GeoLite2-City.mmdb"
        assert GEOIP_COUNTRY_DB == "data/GeoLite2-Country.mmdb"

    def test_lookup_coordinates_no_db(self):
        from providers.geography.geoip import lookup_coordinates

        mock_module = MagicMock()
        mock_module.database.Reader.side_effect = Exception("DB not found")

        with patch.dict("sys.modules", {"geoip2": mock_module, "geoip2.database": mock_module.database}):
            with patch("builtins.__import__", side_effect=_import_geoip2_fail):
                result = lookup_coordinates("1.2.3.4")
                assert result is None

    def test_lookup_coordinates_success(self):
        from providers.geography.geoip import lookup_coordinates

        mock_reader = MagicMock()
        mock_location = MagicMock()
        mock_location.latitude = 52.52
        mock_location.longitude = 13.405
        mock_response = MagicMock()
        mock_response.location = mock_location
        mock_reader.city.return_value = mock_response

        mock_module = MagicMock()
        mock_module.database.Reader.return_value = mock_reader

        with patch.dict("sys.modules", {"geoip2": mock_module, "geoip2.database": mock_module.database}):
            import providers.geography.geoip as geoip_mod

            geoip_mod._reader = None
            result = lookup_coordinates("1.2.3.4")
            assert result == (52.52, 13.405)

    def test_lookup_coordinates_none_coords(self):
        from providers.geography.geoip import lookup_coordinates

        mock_reader = MagicMock()
        mock_location = MagicMock()
        mock_location.latitude = None
        mock_location.longitude = None
        mock_response = MagicMock()
        mock_response.location = mock_location
        mock_reader.city.return_value = mock_response

        mock_module = MagicMock()
        mock_module.database.Reader.return_value = mock_reader

        with patch.dict("sys.modules", {"geoip2": mock_module, "geoip2.database": mock_module.database}):
            import providers.geography.geoip as geoip_mod

            geoip_mod._reader = None
            result = lookup_coordinates("1.2.3.4")
            assert result is None

    def test_lookup_country_code_no_db(self):
        from providers.geography.geoip import lookup_country_code

        mock_module = MagicMock()
        mock_module.database.Reader.side_effect = Exception("DB not found")

        with patch.dict("sys.modules", {"geoip2": mock_module, "geoip2.database": mock_module.database}):
            with patch("builtins.__import__", side_effect=_import_geoip2_fail):
                result = lookup_country_code("1.2.3.4")
                assert result is None

    def test_lookup_country_code_success(self):
        from providers.geography.geoip import lookup_country_code

        mock_reader = MagicMock()
        mock_country = MagicMock()
        mock_country.iso_code = "DE"
        mock_response = MagicMock()
        mock_response.country = mock_country
        mock_reader.country.return_value = mock_response

        mock_module = MagicMock()
        mock_module.database.Reader.return_value = mock_reader

        with patch.dict("sys.modules", {"geoip2": mock_module, "geoip2.database": mock_module.database}):
            import providers.geography.geoip as geoip_mod

            geoip_mod._country_reader = None
            result = lookup_country_code("1.2.3.4")
            assert result == "DE"

    def test_lookup_country_code_no_iso(self):
        from providers.geography.geoip import lookup_country_code

        mock_reader = MagicMock()
        mock_country = MagicMock()
        mock_country.iso_code = None
        mock_response = MagicMock()
        mock_response.country = mock_country
        mock_reader.country.return_value = mock_response

        mock_module = MagicMock()
        mock_module.database.Reader.return_value = mock_reader

        with patch.dict("sys.modules", {"geoip2": mock_module, "geoip2.database": mock_module.database}):
            import providers.geography.geoip as geoip_mod

            geoip_mod._country_reader = None
            result = lookup_country_code("1.2.3.4")
            assert result is None


def _import_geoip2_fail(name, *args, **kwargs):
    if name == "geoip2.database":
        raise ImportError("No module named 'geoip2'")
    return __builtins__.__import__(name, *args, **kwargs)


# ===========================================================================
# geography/ip.py — IP geolocation & geocoding
# ===========================================================================


class TestIpProvider:
    """Tests for backend/providers/geography/ip.py."""

    def test_detect_country_from_ip_empty(self):
        from providers.geography.ip import detect_country_from_ip

        result = detect_country_from_ip("")
        assert result is None

    def test_detect_country_from_ip_private(self):
        from providers.geography.ip import detect_country_from_ip

        result = detect_country_from_ip("192.168.1.1")
        assert result is None

    def test_detect_country_from_ip_loopback(self):
        from providers.geography.ip import detect_country_from_ip

        result = detect_country_from_ip("127.0.0.1")
        assert result is None

    def test_detect_country_from_ip_invalid(self):
        from providers.geography.ip import detect_country_from_ip

        result = detect_country_from_ip("not-an-ip")
        assert result is None

    def test_detect_country_from_ip_success(self):
        from providers.geography.ip import detect_country_from_ip

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "success",
            "countryCode": "DE",
        }

        with patch("providers.geography.ip.httpx.get", return_value=mock_response):
            result = detect_country_from_ip("85.214.132.117")
            assert result == "DE"

    def test_detect_country_from_ip_lowercase_result(self):
        from providers.geography.ip import detect_country_from_ip

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "success",
            "countryCode": "de",
        }

        with patch("providers.geography.ip.httpx.get", return_value=mock_response):
            result = detect_country_from_ip("85.214.132.117")
            assert result == "DE"

    def test_detect_country_from_ip_api_fails_fallback(self):
        from providers.geography.ip import detect_country_from_ip

        mock_response_fail = MagicMock()
        mock_response_fail.status_code = 500

        mock_response_fallback = MagicMock()
        mock_response_fallback.status_code = 200
        mock_response_fallback.json.return_value = {"country_code": "FR"}

        with patch("providers.geography.ip.httpx.get", side_effect=[mock_response_fail, mock_response_fallback]):
            result = detect_country_from_ip("178.32.100.1")
            assert result == "FR"

    def test_detect_country_from_ip_exception_fallback(self):
        from providers.geography.ip import detect_country_from_ip

        mock_response_fallback = MagicMock()
        mock_response_fallback.status_code = 200
        mock_response_fallback.json.return_value = {"country_code": "JP"}

        with patch("providers.geography.ip.httpx.get", side_effect=[Exception("timeout"), mock_response_fallback]):
            result = detect_country_from_ip("1.2.3.4")
            assert result == "JP"

    def test_lookup_ipapi_co_empty(self):
        from providers.geography.ip import lookup_ipapi_co

        result = lookup_ipapi_co("")
        assert result is None

    def test_lookup_ipapi_co_success(self):
        from providers.geography.ip import lookup_ipapi_co

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"country_code": "DE"}

        with patch("providers.geography.ip.httpx.get", return_value=mock_response):
            result = lookup_ipapi_co("85.214.132.117")
            assert result == "DE"

    def test_lookup_ipapi_co_failure(self):
        from providers.geography.ip import lookup_ipapi_co

        with patch("providers.geography.ip.httpx.get", side_effect=Exception("timeout")):
            result = lookup_ipapi_co("1.2.3.4")
            assert result is None

    def test_geocode_location_success(self):
        from providers.geography.ip import geocode_location

        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.json.return_value = {
            "results": [{"name": "Berlin", "latitude": 52.52, "longitude": 13.405}]
        }

        with patch("providers.geography.ip.httpx.get", return_value=mock_response):
            result = geocode_location("Berlin")
            assert result is not None
            assert len(result) == 1
            assert result[0]["name"] == "Berlin"

    def test_geocode_location_failure(self):
        from providers.geography.ip import geocode_location

        with patch("providers.geography.ip.httpx.get", side_effect=Exception("timeout")):
            result = geocode_location("Berlin")
            assert result is None

    def test_geocode_location_count_capped(self):
        from providers.geography.ip import geocode_location

        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.json.return_value = {"results": []}

        with patch("providers.geography.ip.httpx.get", return_value=mock_response) as mock_get:
            geocode_location("Berlin", count=100)
            call_args = mock_get.call_args
            assert call_args[1]["params"]["count"] == 50


# ===========================================================================
# geography/map.py — LocationProvider
# ===========================================================================


class TestLocationProvider:
    """Tests for backend/providers/geography/map.py::LocationProvider."""

    def setup_method(self):
        from providers.geography.map import LocationProvider

        self.provider = LocationProvider()

    def test_init(self):
        assert self.provider._default_timeout == 5.0
        assert self.provider._user_agent == "zozi-location-provider/1.0"

    def test_resolve_ip_success(self):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "ip": "1.2.3.4",
            "country": "Germany",
            "country_code": "DE",
            "region": "Berlin",
            "city": "Berlin",
            "lat": 52.52,
            "lon": 13.405,
            "isp": "ISP",
        }).encode()
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=None)

        mock_req_instance = MagicMock()

        with patch("urllib.request.urlopen", return_value=mock_resp):
            with patch("urllib.request.Request", return_value=mock_req_instance):
                result = self.provider.resolve_ip("1.2.3.4")
                assert result["country"] == "Germany"
                assert result["country_code"] == "DE"

    def test_resolve_ip_all_fail(self):
        with patch("urllib.request.urlopen", side_effect=Exception("timeout")):
            result = self.provider.resolve_ip("1.2.3.4")
            assert result["source"] == "none"
            assert result["country"] == ""

    def test_reverse_geocode_success(self):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "display_name": "Berlin, Germany",
            "address": {
                "road": "Alexanderplatz",
                "city": "Berlin",
                "state": "Berlin",
                "country": "Germany",
                "country_code": "de",
                "postcode": "10178",
            },
        }).encode()
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=None)

        mock_req_instance = MagicMock()

        with patch("urllib.request.urlopen", return_value=mock_resp):
            with patch("urllib.request.Request", return_value=mock_req_instance):
                result = self.provider.reverse_geocode(52.52, 13.405)
                assert result["display_name"] == "Berlin, Germany"
                assert result["city"] == "Berlin"
                assert result["country"] == "Germany"

    def test_reverse_geocode_failure(self):
        with patch("urllib.request.urlopen", side_effect=Exception("timeout")):
            result = self.provider.reverse_geocode(52.52, 13.405)
            assert result["display_name"] == ""
            assert result["latitude"] == 52.52

    def test_calculate_distance_same_point(self):
        distance = self.provider.calculate_distance(52.52, 13.405, 52.52, 13.405)
        assert distance == 0.0

    def test_calculate_distance_known(self):
        # Berlin to Paris ~878 km
        distance = self.provider.calculate_distance(52.52, 13.405, 48.8566, 2.3522)
        assert 800 < distance < 950

    def test_calculate_distance_antipodal(self):
        distance = self.provider.calculate_distance(0, 0, 0, 180)
        assert distance > 19000  # ~20015 km

    def test_get_ip_providers(self):
        providers = self.provider._get_ip_providers()
        assert len(providers) == 2
        assert "ipwho.is" in providers[0]
        assert "ip-api.com" in providers[1]


# ===========================================================================
# geography/rates.py — Currency rate provider
# ===========================================================================


class TestRatesProvider:
    """Tests for backend/providers/geography/rates.py."""

    def setup_method(self):
        from providers.geography.rates import reset_rate_cache

        reset_rate_cache()

    def teardown_method(self):
        from providers.geography.rates import reset_rate_cache

        reset_rate_cache()

    def test_rate_cache_ttl(self):
        from providers.geography.rates import RATE_CACHE_TTL_SECONDS

        assert RATE_CACHE_TTL_SECONDS == 3600

    def test_normalize_currency_code_valid(self):
        from providers.geography.rates import normalize_currency_code

        assert normalize_currency_code("usd") == "USD"
        assert normalize_currency_code("EUR") == "EUR"

    def test_normalize_currency_code_none(self):
        from providers.geography.rates import normalize_currency_code

        assert normalize_currency_code(None) == "OMR"

    def test_normalize_currency_code_empty(self):
        from providers.geography.rates import normalize_currency_code

        assert normalize_currency_code("") == "OMR"

    def test_normalize_currency_code_special_chars(self):
        from providers.geography.rates import normalize_currency_code

        assert normalize_currency_code("us$d") == "USD"

    def test_normalize_currency_code_wrong_length(self):
        from providers.geography.rates import normalize_currency_code

        assert normalize_currency_code("US") == "OMR"
        assert normalize_currency_code("USDD") == "OMR"

    def test_fetch_rates_live(self):
        from providers.geography.rates import fetch_rates

        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.json.return_value = {
            "rates": {"USD": 1.0, "EUR": 0.85, "GBP": 0.73},
        }

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=None)
        mock_client.get = MagicMock(return_value=mock_response)

        with patch("providers.geography.rates.httpx.Client", return_value=mock_client):
            rates, source = fetch_rates()
            assert source == "live"
            assert "USD" in rates
            assert "EUR" in rates
            assert rates["AED"] == Decimal("1")

    def test_fetch_rates_fallback(self):
        from providers.geography.rates import fetch_rates

        with patch("providers.geography.rates.httpx.Client", side_effect=Exception("network down")):
            rates, source = fetch_rates()
            assert source == "fallback"

    def test_fetch_rates_caching(self):
        from providers.geography.rates import fetch_rates

        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.json.return_value = {"rates": {"USD": 1.0}}

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=None)
        mock_client.get = MagicMock(return_value=mock_response)

        with patch("providers.geography.rates.httpx.Client", return_value=mock_client):
            rates1, source1 = fetch_rates()
            rates2, source2 = fetch_rates()
            assert rates1 == rates2
            assert mock_client.get.call_count == 1

    def test_fetch_rates_non_dict_response(self):
        from providers.geography.rates import fetch_rates

        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.json.return_value = {"rates": "not-a-dict"}

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=None)
        mock_client.get = MagicMock(return_value=mock_response)

        with patch("providers.geography.rates.httpx.Client", return_value=mock_client):
            rates, source = fetch_rates()
            assert source == "fallback"

    def test_lookup_currency_from_wikidata_empty(self):
        from providers.geography.rates import lookup_currency_from_wikidata

        assert lookup_currency_from_wikidata("") is None

    def test_lookup_currency_from_wikidata_none(self):
        from providers.geography.rates import lookup_currency_from_wikidata

        assert lookup_currency_from_wikidata(None) is None

    def test_lookup_currency_from_wikidata_success(self):
        from providers.geography.rates import lookup_currency_from_wikidata

        mock_search_resp = MagicMock()
        mock_search_resp.is_success = True
        mock_search_resp.json.return_value = {"search": [{"id": "Q123"}]}

        mock_entity_resp = MagicMock()
        mock_entity_resp.is_success = True
        mock_entity_resp.json.return_value = {
            "entities": {
                "Q123": {
                    "claims": {
                        "P38": [{
                            "mainsnak": {
                                "snaktype": "value",
                                "datavalue": {"value": {"id": "Q48159"}},
                            },
                        }],
                    },
                },
            },
        }

        mock_currency_resp = MagicMock()
        mock_currency_resp.is_success = True
        mock_currency_resp.json.return_value = {
            "entities": {
                "Q48159": {
                    "claims": {
                        "P498": [{
                            "mainsnak": {
                                "snaktype": "value",
                                "datavalue": {"value": {"text": "EUR"}},
                            },
                        }],
                    },
                },
            },
        }

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=None)
        mock_client.get = MagicMock(
            side_effect=[mock_search_resp, mock_entity_resp, mock_currency_resp],
        )

        with patch("providers.geography.rates.httpx.Client", return_value=mock_client):
            result = lookup_currency_from_wikidata("DE")
            assert result == "EUR"

    def test_lookup_currency_from_wikidata_no_search_results(self):
        from providers.geography.rates import lookup_currency_from_wikidata

        mock_search_resp = MagicMock()
        mock_search_resp.is_success = True
        mock_search_resp.json.return_value = {"search": []}

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=None)
        mock_client.get = MagicMock(return_value=mock_search_resp)

        with patch("providers.geography.rates.httpx.Client", return_value=mock_client):
            result = lookup_currency_from_wikidata("ZZ")
            assert result is None

    def test_lookup_currency_from_wikidata_caching(self):
        from providers.geography import rates as rates_mod
        from providers.geography.rates import lookup_currency_from_wikidata

        rates_mod._COUNTRY_CURRENCY_CACHE.clear()

        mock_search_resp = MagicMock()
        mock_search_resp.is_success = True
        mock_search_resp.json.return_value = {"search": [{"id": "Q123"}]}

        mock_entity_resp = MagicMock()
        mock_entity_resp.is_success = True
        mock_entity_resp.json.return_value = {
            "entities": {
                "Q123": {
                    "claims": {
                        "P38": [{
                            "mainsnak": {
                                "snaktype": "value",
                                "datavalue": {"value": {"id": "Q48159"}},
                            },
                        }],
                    },
                },
            },
        }

        mock_currency_resp = MagicMock()
        mock_currency_resp.is_success = True
        mock_currency_resp.json.return_value = {
            "entities": {
                "Q48159": {
                    "claims": {
                        "P498": [{
                            "mainsnak": {
                                "snaktype": "value",
                                "datavalue": {"value": {"text": "EUR"}},
                            },
                        }],
                    },
                },
            },
        }

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=None)
        mock_client.get = MagicMock(
            side_effect=[mock_search_resp, mock_entity_resp, mock_currency_resp],
        )

        with patch("providers.geography.rates.httpx.Client", return_value=mock_client):
            result1 = lookup_currency_from_wikidata("DE")
            result2 = lookup_currency_from_wikidata("DE")
            assert result1 == result2 == "EUR"
            assert mock_client.get.call_count == 3

    def test_reset_rate_cache(self):
        from providers.geography.rates import reset_rate_cache, rate_cache_expiry

        reset_rate_cache()
        assert rate_cache_expiry() == 0.0

    def test_rate_cache_expiry(self):
        from providers.geography.rates import rate_cache_expiry

        expiry = rate_cache_expiry()
        assert isinstance(expiry, float)


# ===========================================================================
# geography/__init__.py — Package exports
# ===========================================================================


class TestGeographyInit:
    """Tests for backend/providers/geography/__init__.py exports."""

    def test_imports_work(self):
        from providers.geography import (
            CountryDetectionProvider,
            LocationProvider,
            CountrySearchProvider,
            RATE_CACHE_TTL_SECONDS,
            normalize_currency_code,
            fetch_rates,
            lookup_currency_from_wikidata,
            reset_rate_cache,
            rate_cache_expiry,
        )

        assert CountryDetectionProvider is not None
        assert LocationProvider is not None
        assert CountrySearchProvider is not None
        assert RATE_CACHE_TTL_SECONDS == 3600
        assert callable(normalize_currency_code)
        assert callable(fetch_rates)
        assert callable(lookup_currency_from_wikidata)
        assert callable(reset_rate_cache)
        assert callable(rate_cache_expiry)


# ===========================================================================
# Edge cases and integration-style tests
# ===========================================================================


class TestEdgeCases:
    """Cross-module edge case tests."""

    def test_invalid_ip_address_formats(self):
        from providers.geography.ip import detect_country_from_ip

        invalid_ips = ["", "abc", "999.999.999.999", "1.2.3", "1.2.3.4.5"]
        for ip in invalid_ips:
            result = detect_country_from_ip(ip)
            assert result is None

    def test_empty_coordinates(self):
        from providers.geography.map import LocationProvider

        provider = LocationProvider()
        distance = provider.calculate_distance(0.0, 0.0, 0.0, 0.0)
        assert distance == 0.0

    def test_negative_coordinates(self):
        from providers.geography.map import LocationProvider

        provider = LocationProvider()
        distance = provider.calculate_distance(-33.8688, 151.2093, -37.8136, 144.9631)
        assert distance > 0

    def test_currency_code_edge_cases(self):
        from providers.geography.rates import normalize_currency_code

        assert normalize_currency_code(None) == "OMR"
        assert normalize_currency_code("") == "OMR"
        assert normalize_currency_code("   ") == "OMR"
        assert normalize_currency_code("12a3b") == "OMR"

    def test_country_search_special_characters(self):
        from providers.geography.country import CountrySearchProvider

        provider = CountrySearchProvider()
        results = provider.search_country("@#$%")
        assert results == []
