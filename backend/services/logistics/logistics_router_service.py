"""
Logistics Router Service — DB operations extracted from logistics and imports routers.
All functions accept `db: Session` as their first parameter.
"""
from datetime import datetime, timezone
from typing import Any, Optional, cast

from fastapi import HTTPException
from sqlalchemy.orm import Session, selectinload

from data.models import Shipment, ShipmentEvent
from data.services_write_helpers import add_and_flush, commit_and_refresh


def get_shipment_by_scan_code(db: Session, code: str) -> Shipment:
    shipment = db.query(Shipment).filter(
        (Shipment.tracking_number == code) | (Shipment.id == (int(code) if code.isdigit() else -1))
    ).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    return shipment


def serialize_shipment_for_scan(shipment: Shipment) -> dict:
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


def update_shipment_status_direct(
    db: Session,
    shipment_id: int,
    status: str,
    note: Optional[str] = None,
) -> dict:
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    new_status = str(status).strip()
    shipment.status = new_status
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if new_status == "delivered" and not shipment.actual_delivery:
        shipment.actual_delivery = now
    elif new_status == "shipped" and not shipment.shipped_at:
        shipment.shipped_at = now
    event = ShipmentEvent(
        shipment_id=shipment_id,
        event_type="status_change",
        status_after=new_status,
        location=shipment.current_hub,
        notes=note or "Admin status update",
        created_at=now,
    )
    add_and_flush(db, event)
    commit_and_refresh(db, shipment)
    return {
        "id": shipment.id,
        "order_id": shipment.order_id,
        "status": shipment.status,
        "carrier_name": shipment.carrier_name,
        "tracking_number": shipment.tracking_number,
        "distribution_channel": shipment.distribution_channel,
        "current_hub": shipment.current_hub,
    }


def get_shipment_summary(db: Session, shipment_id: int) -> dict:
    shipment = db.query(Shipment).options(
        selectinload(Shipment.order),
        selectinload(Shipment.carrier),
        selectinload(Shipment.assigned_partner),
    ).filter(Shipment.id == shipment_id).first()
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
    }


def get_import_shipment(db: Session, shipment_id: int):
    from data.models import ImportShipment
    s = db.query(ImportShipment).filter(ImportShipment.id == shipment_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Shipment not found")
    return s