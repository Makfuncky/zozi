from __future__ import annotations

"""GeoIP (MaxMind) provider.

Encapsulates the raw ``geoip2`` SDK access so middleware/services no longer
import the vendor package directly. The SDK stays an optional dependency:
it is only imported lazily inside the lookup call, mirroring the pattern used
by the other geography providers.
"""

import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

HAS_GEOIP = True

# City-level database (provides lat/lon for impossible-travel detection).
GEOIP_CITY_DB = "data/GeoLite2-City.mmdb"

# Country-level database (provides an ISO country code for country detection).
GEOIP_COUNTRY_DB = "data/GeoLite2-Country.mmdb"

_reader = None
_country_reader = None


def lookup_coordinates(ip: str) -> Optional[Tuple[float, float]]:
    """Return ``(latitude, longitude)`` for ``ip`` via the GeoLite2-City DB.

    Returns ``None`` when the database is missing/unreadable or the lookup
    fails, so callers can fall back to their own caching/defaults.
    """
    global _reader
    try:
        import geoip2.database

        if _reader is None:
            try:
                _reader = geoip2.database.Reader(GEOIP_CITY_DB)
            except Exception as exc:
                logger.warning("Failed to open GeoIP City database %s: %s", GEOIP_CITY_DB, exc)
                return None
        if _reader is None:
            return None

        response = _reader.city(ip)
        lat = response.location.latitude
        lon = response.location.longitude
        if lat is not None and lon is not None:
            return (lat, lon)
    except Exception as exc:
        logger.debug("GeoIP city lookup failed for %s: %s", ip, exc)
    return None


def lookup_country_code(ip: str) -> Optional[str]:
    """Return the ISO country code for ``ip`` via the GeoLite2-Country DB.

    Returns ``None`` when the database is missing/unreadable or the lookup
    fails, so callers can fall back to other providers / defaults.
    """
    global _country_reader
    try:
        import geoip2.database

        if _country_reader is None:
            try:
                _country_reader = geoip2.database.Reader(GEOIP_COUNTRY_DB)
            except Exception as exc:
                logger.warning("Failed to open GeoIP Country database %s: %s", GEOIP_COUNTRY_DB, exc)
                return None
        if _country_reader is None:
            return None

        response = _country_reader.country(ip)
        if response and response.country and response.country.iso_code:
            return response.country.iso_code
    except Exception as exc:
        logger.debug("GeoIP country lookup failed for %s: %s", ip, exc)
    return None


__all__ = ["lookup_coordinates", "lookup_country_code", "GEOIP_CITY_DB", "GEOIP_COUNTRY_DB"]
