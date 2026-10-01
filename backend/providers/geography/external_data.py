from __future__ import annotations

"""External country-data provider.

Third-party country/enrichment vendor HTTP calls (RestCountries, World Bank,
GeoDB Cities, Nager.Date) are encapsulated here so the data orchestrator service
orchestrates through these helpers instead of performing vendor HTTP requests
directly. Caching (Redis) remains the service's responsibility.
"""

import logging
from typing import Any, Dict, List

try:
    import aiohttp
    HAS_EXTERNAL_DATA = True
except ImportError:
    HAS_EXTERNAL_DATA = False
    aiohttp = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

REST_COUNTRIES_URL = "https://restcountries.com/v3.1/alpha/{country_code}"
WORLD_BANK_URL = "https://api.worldbank.org/v2/country/{country_code}?format=json"
GEODB_CITIES_URL = "https://api.geodb-cities.com/v1/cities?country={country_code}&limit=1000"
NAGER_DATE_URL = "https://date.nager.at/v3/PublicHolidays/{year}/{country_code}"


async def fetch_restcountries(session: aiohttp.ClientSession, country_code: str) -> Dict[str, Any]:
    """Fetch country identity data from RestCountries."""
    url = REST_COUNTRIES_URL.format(country_code=country_code)
    async with session.get(url) as resp:
        if resp.status == 200:
            data = await resp.json()
            return data[0] if data else {}
        return {}


async def fetch_worldbank(session: aiohttp.ClientSession, country_code: str) -> Any:
    """Fetch economic indicator data from the World Bank API."""
    url = WORLD_BANK_URL.format(country_code=country_code)
    async with session.get(url) as resp:
        if resp.status == 200:
            data = await resp.json()
            if isinstance(data, list) and len(data) > 1:
                return data[1] if data[1] else []
            return {}
        return {}


async def fetch_geodb_cities(session: aiohttp.ClientSession, country_code: str) -> List[Any]:
    """Fetch cities from the GeoDB Cities API."""
    url = GEODB_CITIES_URL.format(country_code=country_code)
    async with session.get(url) as resp:
        if resp.status == 200:
            data = await resp.json()
            return data.get("data", [])
        return []


async def fetch_nager_holidays(
    session: aiohttp.ClientSession, country_code: str, year: int = 2024
) -> List[Any]:
    """Fetch public holidays from Nager.Date."""
    url = NAGER_DATE_URL.format(year=year, country_code=country_code)
    async with session.get(url) as resp:
        if resp.status == 200:
            return await resp.json()
        return []


__all__ = [
    "REST_COUNTRIES_URL",
    "WORLD_BANK_URL",
    "GEODB_CITIES_URL",
    "NAGER_DATE_URL",
    "fetch_restcountries",
    "fetch_worldbank",
    "fetch_geodb_cities",
    "fetch_nager_holidays",
]
