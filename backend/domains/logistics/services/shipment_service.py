"""Shipment write operations (logistics domain).

Owns the DB writes for shipment creation, updates, event creation and
admin status changes. Routers must not mutate the session directly.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from _legacy.models import Shipment, ShipmentEvent
import structlog
logger = structlog.get_logger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def create_shipment(db: Session, data: dict[str, Any]) -> Shipment:
    s = Shipment(**data)
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


def update_shipment(db: Session, shipment_id: int, data: dict[str, Any]) -> Shipment:
    s = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Not found")
    for k, v in data.items():
        setattr(s, k, v)
    db.commit()
    db.refresh(s)
    return s


def add_shipment_event(
    db: Session, shipment_id: int, user_id: int, data: dict[str, Any]
) -> ShipmentEvent:
    s = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Not found")
    event = ShipmentEvent(shipment_id=shipment_id, created_by=user_id, **data)
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def admin_set_shipment_status(
    db: Session,
    shipment_id: int,
    new_status: str,
    note: str = "Admin status update",
) -> dict:
    """Admin endpoint to update a shipment status directly (bypasses supplier check)."""
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    now = _utcnow()
    shipment.status = new_status
    if new_status == "delivered" and not shipment.actual_delivery:
        shipment.actual_delivery = now
    elif new_status == "shipped" and not shipment.shipped_at:
        shipment.shipped_at = now
    event = ShipmentEvent(
        shipment_id=shipment_id,
        event_type="status_change",
        status_after=new_status,
        location=shipment.current_hub,
        notes=note,
        created_at=now,
    )
    db.add(event)
    db.commit()
    db.refresh(shipment)
    return {
        "id": shipment.id,
        "order_id": shipment.order_id,
        "status": shipment.status,
        "carrier_name": shipment.carrier_name,
        "tracking_number": shipment.tracking_number,
        "distribution_channel": shipment.distribution_channel,
        "current_hub": shipment.current_hub,
    }


def lookup_shipment_by_code(db: Session, code: str) -> dict[str, Any]:
    """Look up a shipment by tracking number or scan code (admin scan lookup).

    Behaviour-preserving extraction of the inline handler in
    ``routers.logistics_logistics_status.scan_lookup_shipment``.
    """
    shipment = db.query(Shipment).filter(
        (Shipment.tracking_number == code)
        | (Shipment.id == (int(code) if code.isdigit() else -1))
    ).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    return {
        "id": shipment.id,
        "order_id": shipment.order_id,
        "status": shipment.status,
        "carrier_name": shipment.carrier_name,
        "tracking_number": shipment.tracking_number,
        "distribution_channel": shipment.distribution_channel,
        "current_hub": shipment.current_hub,
        "shipping_address": (shipment.order.shipping_address if shipment.order else None),
        "created_at": shipment.created_at.isoformat() if shipment.created_at else None,
        "updated_at": shipment.updated_at.isoformat() if shipment.updated_at else None,
    }
