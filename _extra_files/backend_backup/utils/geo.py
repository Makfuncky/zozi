"""Geographic helper utilities.

Lightweight, dependency-free geo helpers used by the auth and location services.
"""
from __future__ import annotations

import math
from typing import Any, Optional


def geocode(address: str, **kwargs: Any) -> Optional[dict]:
    """Return a coarse geocode result, or ``None`` if unavailable."""
    return None


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in kilometres between two coordinates."""
    r = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


__all__ = ["geocode", "haversine_distance"]
