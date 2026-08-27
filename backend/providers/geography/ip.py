from __future__ import annotations

"""IP geolocation & geocoding provider.

Third-party geo vendor HTTP calls (IP-API, ipapi.co, Open-Meteo geocoding) are
encapsulated here so the geography services orchestrate through these helpers
instead of performing vendor HTTP requests directly.
"""

import ipaddress
import logging
from typing import Any, Dict, List, Optional

try:
    import httpx
    HAS_IP_GEO = True
except ImportError:
    HAS_IP_GEO = False
    httpx = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

_IPAPI_BASE_URL = "http://ip-api.com/json/"
_IPICO_BASE_URL = "https://ipapi.co/{}/json/"
_OPEN_METEO_GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
_REQUEST_TIMEOUT = 5.0


def detect_country_from_ip(ip_address: str) -> Optional[str]:
    """Detect a country code from an IP using IP-API, falling back to ipapi.co.

    Private/loopback addresses and invalid input return ``None`` (no external
    call is made).
    """
    if not ip_address:
        return None
    try:
        ip_obj = ipaddress.ip_address(ip_address)
        if ip_obj.is_private:
            return None
    except ValueError:
        return None
    if ip_address.startswith("127."):
        return None

    try:
        response = httpx.get(
            f"{_IPAPI_BASE_URL}{ip_address}",
            params={"fields": "countryCode,country,city,region,query"},
            timeout=_REQUEST_TIMEOUT,
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success" and data.get("countryCode"):
                return data["countryCode"].upper()
    except Exception as exc:
        logger.warning("IP-API lookup failed for %s: %s", ip_address, exc)

    return _lookup_ipapi_co(ip_address)


def _lookup_ipapi_co(ip_address: str) -> Optional[str]:
    try:
        response = httpx.get(_IPICO_BASE_URL.format(ip_address), timeout=_REQUEST_TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            if data.get("country_code"):
                return data["country_code"].upper()
    except Exception as exc:
        logger.warning("ipapi.co lookup failed for %s: %s", ip_address, exc)
    return None


def lookup_ipapi_co(ip: str) -> Optional[str]:
    """Public ipapi.co lookup wrapper (used as a fallback by country detection)."""
    if not ip:
        return None
    return _lookup_ipapi_co(ip)


def geocode_location(
    name: str,
    *,
    count: int = 10,
    language: str = "en",
    timeout: float = 8.0,
) -> Optional[List[Dict[str, Any]]]:
    """Geocode a place name via Open-Meteo; returns the ``results`` list or None."""
    try:
        resp = httpx.get(
            _OPEN_METEO_GEOCODING_URL,
            params={"name": name, "count": min(count, 50), "language": language, "format": "json"},
            timeout=timeout,
        )
        if resp.is_success:
            return resp.json().get("results", [])
    except Exception as exc:
        logger.warning("Open-Meteo geocoding failed for %s: %s", name, exc)
    return None


__all__ = ["detect_country_from_ip", "lookup_ipapi_co", "geocode_location"]
