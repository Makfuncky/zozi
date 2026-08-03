"""
Curated city lists — used as fallback when GeoNames / GeoDB APIs are unavailable.

Each entry is a flat list of ``dict`` objects with at least *name* and,
optionally, *latitude*, *longitude*, *population*, and *is_capital*.

Add cities here as the platform expands into new countries.
"""
from __future__ import annotations

from typing import Any

CURATED_CITIES: dict[str, list[dict[str, Any]]] = {
    "OM": [
        {"name": "Muscat", "latitude": 23.5880, "longitude": 58.3829, "population": 1421409, "is_capital": True},
        {"name": "Seeb", "latitude": 23.6800, "longitude": 58.1900, "population": 302992, "is_capital": False},
        {"name": "Salalah", "latitude": 17.0197, "longitude": 54.0895, "population": 331949, "is_capital": False},
        {"name": "Sohar", "latitude": 24.3420, "longitude": 56.7200, "population": 221274, "is_capital": False},
        {"name": "Nizwa", "latitude": 22.9333, "longitude": 57.5333, "population": 85000, "is_capital": False},
        {"name": "Sur", "latitude": 22.5667, "longitude": 59.6500, "population": 66000, "is_capital": False},
    ],
    "AE": [
        {"name": "Abu Dhabi", "latitude": 24.4539, "longitude": 54.3773, "population": 1483000, "is_capital": True},
        {"name": "Dubai", "latitude": 25.2048, "longitude": 55.2708, "population": 3331000, "is_capital": False},
        {"name": "Sharjah", "latitude": 25.3573, "longitude": 55.4033, "population": 1400000, "is_capital": False},
        {"name": "Al Ain", "latitude": 24.2075, "longitude": 55.7447, "population": 766000, "is_capital": False},
        {"name": "Ajman", "latitude": 25.4167, "longitude": 55.4333, "population": 490000, "is_capital": False},
    ],
    "SA": [
        {"name": "Riyadh", "latitude": 24.7136, "longitude": 46.6753, "population": 7660000, "is_capital": True},
        {"name": "Jeddah", "latitude": 21.5433, "longitude": 39.1728, "population": 3985000, "is_capital": False},
        {"name": "Mecca", "latitude": 21.4225, "longitude": 39.8262, "population": 2000000, "is_capital": False},
        {"name": "Medina", "latitude": 24.4711, "longitude": 39.6108, "population": 1200000, "is_capital": False},
        {"name": "Dammam", "latitude": 26.4333, "longitude": 50.1000, "population": 1100000, "is_capital": False},
    ],
    "BH": [
        {"name": "Manama", "latitude": 26.2285, "longitude": 50.5860, "population": 577000, "is_capital": True},
        {"name": "Muharraq", "latitude": 26.2572, "longitude": 50.6100, "population": 176000, "is_capital": False},
        {"name": "Riffa", "latitude": 26.1300, "longitude": 50.5550, "population": 111000, "is_capital": False},
    ],
    "KW": [
        {"name": "Kuwait City", "latitude": 29.3697, "longitude": 47.9783, "population": 2976000, "is_capital": True},
        {"name": "Al Ahmadi", "latitude": 29.0769, "longitude": 48.0839, "population": 637000, "is_capital": False},
        {"name": "Hawalli", "latitude": 29.3328, "longitude": 48.0286, "population": 164000, "is_capital": False},
    ],
    "QA": [
        {"name": "Doha", "latitude": 25.2854, "longitude": 51.5310, "population": 1450000, "is_capital": True},
        {"name": "Al Rayyan", "latitude": 25.2919, "longitude": 51.4244, "population": 589000, "is_capital": False},
        {"name": "Al Wakrah", "latitude": 25.1714, "longitude": 51.6072, "population": 87970, "is_capital": False},
    ],
}


def get_cities(country_code: str) -> list[dict[str, Any]]:
    """Return a list of curated cities for *country_code*, or an empty list."""
    return CURATED_CITIES.get(country_code.upper(), [])