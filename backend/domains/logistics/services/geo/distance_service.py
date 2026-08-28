from __future__ import annotations

"""Distance service — distance calculations for logistics."""

from typing import Any, Optional
from math import radians, cos, sin, sqrt, atan2
from sqlalchemy.orm import Session
from domains.governance.models.core import CityDistanceMatrix
from domains.logistics.services.partners.pricing_service import normalize_city_name, normalize_country_code


def haversine_km(lat_a: float, lng_a: float, lat_b: float, lng_b: float) -> float:
    """Calculate the great-circle distance between two points on Earth using the Haversine formula."""
    radius_km = 6371.0
    d_lat = radians(lat_b - lat_a)
    d_lng = radians(lng_b - lng_a)
    a = sin(d_lat / 2) ** 2 + cos(radians(lat_a)) * cos(radians(lat_b)) * sin(d_lng / 2) ** 2
    return 2 * radius_km * asin(sqrt(a))


def lookup_city_distance_km(
    db: Session,
    *,
    origin_country_code: str | None,
    origin_city_name: str | None,
    destination_country_code: str | None,
    destination_city_name: str | None,
) -> float:
    """Return the distance in km between an origin/destination city pair from the distance matrix."""
    if not (origin_country_code and origin_city_name and destination_country_code and destination_city_name):
        return 0.0

    origin_cc = normalize_country_code(origin_country_code)
    dest_cc = normalize_country_code(destination_country_code)
    origin_key = normalize_city_name(origin_city_name)
    dest_key = normalize_city_name(destination_city_name)

    row = (
        db.query(CityDistanceMatrix)
        .filter(
            CityDistanceMatrix.origin_country_code == origin_cc,
            CityDistanceMatrix.destination_country_code == dest_cc,
        )
        .all()
    )
    for entry in row:
        if (
            normalize_city_name(str(getattr(entry, "origin_city_name", None))) == origin_key
            and normalize_city_name(str(getattr(entry, "destination_city_name", None))) == dest_key
        ):
            return float(getattr(entry, "distance_km", 0) or 0)
    return 0.0
