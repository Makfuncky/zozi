"""Geo-resolution helpers for the location API.

Thin, dependency-light wrappers around the existing geocoding capabilities so
routers can resolve IP locations and reverse-geocode coordinates without
pulling the full map service into the request path.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from utils.geo import geocode as _geocode  # noqa: F401  (reuse existing geo utils)


def resolve_ip_location(ip: str, **kwargs: Any) -> Dict[str, Any]:
    """Best-effort mapping from a client IP to a coarse location.

    In production this would call a GeoIP provider; here we return a neutral
    structure so callers can degrade gracefully when no provider is
    configured.
    """
    # Placeholder implementation: real GeoIP lookup would go here.
    return {
        "ip": ip,
        "country_code": None,
        "city": None,
        "latitude": None,
        "longitude": None,
        "resolved": False,
    }


def reverse_geocode(latitude: float, longitude: float, **kwargs: Any) -> Dict[str, Any]:
    """Resolve a human-readable address for a coordinate pair."""
    try:
        from services.map import MapService

        svc = MapService()
        return svc.reverse_geocode(latitude=latitude, longitude=longitude)
    except Exception:
        # Degrade gracefully if the map service is unavailable.
        return {
            "latitude": latitude,
            "longitude": longitude,
            "address": None,
            "resolved": False,
        }
