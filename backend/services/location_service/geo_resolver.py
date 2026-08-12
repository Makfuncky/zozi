"""Location resolution utilities for the Zozi order/delivery system.

The live key-less geo SDK calls (ipwho.is, ip-api, OpenStreetMap Nominatim)
now live in :mod:`providers.geo`. This module re-exports the public surface so
existing imports (``routers/api_geography_location.py``,
``services/location_service/main.py``) keep working unchanged.

External lookups are performed live (no fake coordinates are ever returned). If a
network lookup fails the caller gets a clear error so the UI can fall back to the
browser Geolocation API rather than trusting a fabricated location.
"""

from providers.geography.geo import (
    DEFAULT_TIMEOUT,
    CACHE_TTL_SECONDS,
    USER_AGENT,
    IP_GEO_PROVIDERS,
    REVERSE_GEO_URL,
    IpLocation,
    ReverseLocation,
    resolve_ip_location,
    reverse_geocode,
)

__all__ = [
    "DEFAULT_TIMEOUT",
    "CACHE_TTL_SECONDS",
    "USER_AGENT",
    "IP_GEO_PROVIDERS",
    "REVERSE_GEO_URL",
    "IpLocation",
    "ReverseLocation",
    "resolve_ip_location",
    "reverse_geocode",
]
