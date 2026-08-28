from __future__ import annotations

"""Routing service — route planning for logistics."""

from datetime import datetime
from typing import Any
from math import radians, cos, sin, sqrt, atan2
from infrastructure.utils.datetime_utils import utcnow as _utcnow


def _haversine_km(lat_a: float, lng_a: float, lat_b: float, lng_b: float) -> float:
    radius_km = 6371.0
    d_lat = radians(lat_b - lat_a)
    d_lng = radians(lng_b - lng_a)
    a = sin(d_lat / 2) ** 2 + cos(radians(lat_a)) * cos(radians(lat_b)) * sin(d_lng / 2) ** 2
    return 2 * radius_km * asin(sqrt(a))


def build_route_plan(points: list[dict]) -> dict:
    """Build an optimized route plan from a list of stops using nearest-neighbor heuristic."""
    if not points:
        return {
            "generated_at": None,
            "total_stops": 0,
            "estimated_distance_km": 0.0,
            "estimated_duration_hours": 0.0,
            "stops": [],
        }

    remaining = [dict(point) for point in points]
    ordered: list[dict] = []
    total_distance = 0.0

    current = remaining.pop(0)
    ordered.append({**current, "stop_number": 1, "distance_from_previous_km": 0.0})

    while remaining:
        next_index = 0
        next_distance = _haversine_km(
            float(current["latitude"]),
            float(current["longitude"]),
            float(remaining[0]["latitude"]),
            float(remaining[0]["longitude"]),
        )
        for index, candidate in enumerate(remaining[1:], start=1):
            candidate_distance = _haversine_km(
                float(current["latitude"]),
                float(current["longitude"]),
                float(candidate["latitude"]),
                float(candidate["longitude"]),
            )
            if candidate_distance < next_distance:
                next_index = index
                next_distance = candidate_distance
        current = remaining.pop(next_index)
        total_distance += next_distance
        ordered.append(
            {
                **current,
                "stop_number": len(ordered) + 1,
                "distance_from_previous_km": round(next_distance, 1),
            }
        )

    return {
        "generated_at": _utcnow().isoformat(),
        "total_stops": len(ordered),
        "estimated_distance_km": round(total_distance, 1),
        "estimated_duration_hours": round((total_distance / 40.0) + max(0, len(ordered) - 1) * 0.15, 1),
        "stops": ordered,
    }
