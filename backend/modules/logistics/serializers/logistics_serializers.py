"""Logistics module serializers (per-actor view models).

Per ARCHITECTURE_DIAGRAM.md §3, modules/{actor}/serializers/ holds
response shaping helpers that transform domain service output into
logistics-facing API responses.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class ShipmentTrackingResponse(BaseModel):
    """Logistics-facing shipment tracking response."""
    shipment_id: int
    tracking_number: str
    status: str
    carrier: Optional[str] = None
    estimated_delivery: Optional[datetime] = None
    last_event: Optional[str] = None


class LogisticsPartnerSummary(BaseModel):
    """Logistics-facing partner summary."""
    id: int
    name: str
    rating: float = 0.0
    active_shipments: int = 0
    country_codes: List[str] = []


def shape_tracking_for_logistics(tracking: Dict[str, Any]) -> ShipmentTrackingResponse:
    """Shape domain tracking data into logistics-facing response."""
    return ShipmentTrackingResponse(
        shipment_id=tracking.get("shipment_id", 0),
        tracking_number=tracking.get("tracking_number", ""),
        status=tracking.get("status", "unknown"),
        carrier=tracking.get("carrier"),
        estimated_delivery=tracking.get("estimated_delivery"),
        last_event=tracking.get("last_event"),
    )


__all__ = [
    "ShipmentTrackingResponse",
    "LogisticsPartnerSummary",
    "shape_tracking_for_logistics",
]
