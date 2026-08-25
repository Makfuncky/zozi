from __future__ import annotations

"""Country auto-populate external HTTP provider.

Raw third-party HTTP GET calls used by ``services.geography.country_auto_populate``
(RestCountries, World Bank, GeoDB, Nager.Date, VAT-Rates) are encapsulated here so
the auto-populate service keeps only domain normalization + retry logic. Returns
parsed JSON on HTTP 200, ``None`` otherwise; network errors propagate as
``httpx.RequestError`` so the caller's retry wrapper can handle them.
"""

import json
import logging
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 10.0


class CountryHttpError(Exception):
    """Raised on network failure talking to a country-data vendor API."""

_REST_COUNTRIES_URL = "https://restcountries.com/v3.1"
_WORLD_BANK_URL = "https://api.worldbank.org/v2/country"
_GEODB_CITIES_URL = "https://geodb-studios.github.io/rest-countries/api/{code}.json"
_NAGER_DATE_URL = "https://date.nager.at/api/v3/publicholidays/{year}/{code}"
_VAT_RATES_URL = "https://api.vat-rates.com/api/rates/{country_code}"

_NAGER_ISO_MAP = {"GB": "GB", "AE": "AE", "SA": "SA", "OM": "OM", "KW": "KW", "BH": "BH"}


async def get_json(
    url: str, *, params: Optional[Dict[str, Any]] = None, timeout: float = DEFAULT_TIMEOUT
) -> Optional[Any]:
    """GET a URL and return parsed JSON, or ``None`` on non-2xx / decode failure."""
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(url, params=params)
            if resp.status_code != 200:
                return None
            return resp.json()
    except httpx.RequestError as exc:
        raise CountryHttpError(str(exc)) from exc
    except (
        json.JSONDecodeError,
        TimeoutError,
        ValueError,
        OSError,
    ) as exc:
        logger.debug("get_json failed for %s: %s", url, exc)
        return None


async def fetch_restcountries_raw(term: str) -> Optional[Any]:
    t = (term or "").strip()
    if not t:
        return None
    if t.isalpha() and len(t) in (2, 3):
        return await get_json(f"{_REST_COUNTRIES_URL}/alpha/{t.upper()}")
    data = await get_json(f"{_REST_COUNTRIES_URL}/name/{t}", params={"fullText": "true"})
    if data is None:
        data = await get_json(f"{_REST_COUNTRIES_URL}/name/{t}")
    return data


async def fetch_worldbank_indicator_raw(
    code: str, indicator: str, per_page: int = 5
) -> Optional[Any]:
    return await get_json(
        f"{_WORLD_BANK_URL}/{code}/indicator/{indicator}",
        params={"format": "json", "per_page": per_page},
    )


async def fetch_geodb_cities_raw(code: str) -> Optional[Any]:
    return await get_json(_GEODB_CITIES_URL.format(code=code))


async def fetch_nager_holidays_raw(code: str, year: int) -> Optional[Any]:
    nager_code = _NAGER_ISO_MAP.get(code.upper(), code.upper())
    return await get_json(_NAGER_DATE_URL.format(year=year, code=nager_code))


async def fetch_vat_rate_raw(country_code: str) -> Optional[Any]:
    return await get_json(_VAT_RATES_URL.format(country_code=country_code))


__all__ = [
    "DEFAULT_TIMEOUT",
    "CountryHttpError",
    "get_json",
    "fetch_restcountries_raw",
    "fetch_worldbank_indicator_raw",
    "fetch_geodb_cities_raw",
    "fetch_nager_holidays_raw",
    "fetch_vat_rate_raw",
]
