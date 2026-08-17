"""Assigned-shipment read service for logistics partners.

Extracted from the surface router so HTTP/presentation concerns stay out of the
data layer (routers -> controllers -> services).
"""
from __future__ import annotations

from typing import Any, Dict, List

from fastapi import HTTPException
from sqlalchemy.orm import Session

from _legacy.models import LogisticsPartner, Shipment


def serialize_shipment(shipment: Shipment) -> Dict[str, Any]:
    """Project a Shipment ORM row into the API response shape."""
    return {
        "id": shipment.id,
        "order_id": shipment.order_id,
        "status": shipment.status,
        "tracking_number": shipment.tracking_number,
        "carrier_name": shipment.carrier_name,
        "distribution_channel": shipment.distribution_channel,
        "estimated_delivery": (
            shipment.estimated_delivery.isoformat() if shipment.estimated_delivery else None
        ),
        "actual_delivery": (
            shipment.actual_delivery.isoformat() if shipment.actual_delivery else None
        ),
    }


def list_assigned_shipments(db: Session, user: Any) -> List[Dict[str, Any]]:
    """Return the shipments assigned to the logistics partner linked to ``user``.

    Raises 404 if the authenticated user is not linked to a logistics partner.
    """
    partner = (
        db.query(LogisticsPartner)
        .filter(LogisticsPartner.user_id == user.id)
        .first()
    )
    if not partner:
        raise HTTPException(status_code=404, detail="Logistics partner not found for user")

    shipments = (
        db.query(Shipment)
        .filter(Shipment.assigned_partner_id == partner.id)
        .all()
    )
    return [serialize_shipment(s) for s in shipments]
