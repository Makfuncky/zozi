"""Auto-migrated service logic from routers/logistics.py."""
from __future__ import annotations

from typing import Any

from fastapi import Depends, HTTPException

from sqlalchemy.orm import Session

import modules.orders.routers.logistics_controller as ctrl

from infrastructure.database.database import get_db

from infrastructure.utils.dependencies import get_current_user

async def get_logistics_summary(db: Session, current_user: dict):
    return await ctrl.get_logistics_summary(current_user, db)

async def get_carriers(db: Session, current_user: dict):
    return await ctrl.get_carriers(current_user, db)

async def create_carrier(data: dict[str, Any], db: Session, current_user: dict):
    return await ctrl.create_carrier(data, current_user, db)

async def delete_carrier(carrier_id: int, db: Session, current_user: dict):
    return await ctrl.delete_carrier(carrier_id, current_user, db)

async def get_shipping_zones(db: Session, current_user: dict):
    return await ctrl.get_shipping_zones(current_user, db)

async def upsert_shipping_zone(data: dict[str, Any], db: Session, current_user: dict):
    return await ctrl.upsert_shipping_zone(data, current_user, db)

async def update_shipping_zone(zone_id: int, data: dict[str, Any], db: Session, current_user: dict):
    data["id"] = zone_id
    return await ctrl.upsert_shipping_zone(data, current_user, db)

async def delete_shipping_zone(zone_id: int, db: Session, current_user: dict):
    return await ctrl.delete_shipping_zone(zone_id, current_user, db)

async def get_orders_to_fulfil(limit: int, offset: int, db: Session, current_user: dict):
    return await ctrl.get_orders_to_fulfil(current_user, db, limit=limit, offset=offset)

async def create_shipment(data: dict[str, Any], db: Session, current_user: dict):
    return await ctrl.create_shipment(data, current_user, db)

async def scan_lookup_shipment(code: str, db: Session, current_user: dict):
    """Look up a shipment by tracking number or scan code. Admin only."""
    if str(current_user.get("role") or "").lower() not in ("admin", "sub_admin", "moderator", "support"):
        raise HTTPException(status_code=403, detail="Admin access required")
    from _legacy.models import Shipment
    shipment = db.query(Shipment).filter(
        (Shipment.tracking_number == code) | (Shipment.id == (int(code) if code.isdigit() else -1))
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

async def admin_update_shipment_status(shipment_id: int, data: dict[str, Any], db: Session, current_user: dict):
    """Admin endpoint to update a shipment status directly (bypasses supplier check)."""
    if str(current_user.get("role") or "").lower() not in ("admin", "sub_admin", "moderator", "support"):
        raise HTTPException(status_code=403, detail="Admin access required")
    from datetime import datetime, timezone

    from _legacy.models import Shipment, ShipmentEvent
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    new_status = data.get("status")
    if new_status:
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
            notes=data.get("note", "Admin status update"),
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

async def get_active_shipments(db: Session, current_user: dict):
    return await ctrl.get_active_shipments(current_user, db)

async def get_shipment_history(page: int, per_page: int, db: Session, current_user: dict):
    return await ctrl.get_shipment_history(current_user, db, page=page, per_page=per_page)

async def get_shipment_events(shipment_id: int, db: Session, current_user: dict):
    return await ctrl.get_shipment_events(shipment_id, current_user, db)

async def scan_shipment_event(shipment_id: int, data: dict[str, Any], db: Session, current_user: dict):
    return await ctrl.scan_shipment_event(shipment_id, data, current_user, db)

async def update_shipment_status(shipment_id: int, data: dict[str, Any], db: Session, current_user: dict):
    return await ctrl.update_shipment_status(shipment_id, data, current_user, db)

async def get_distribution_channels(db: Session, current_user: dict):
    return await ctrl.get_distribution_channels(current_user, db)

async def update_shipment_event_gps(event_id: int, data: dict[str, Any], db: Session, current_user: dict):
    """Attach GPS coordinates to a shipment event (supplier or admin).

    Body: ``{"latitude": float, "longitude": float}``
    """
    try:
        lat = float(data["latitude"])
        lng = float(data["longitude"])
    except (KeyError, TypeError, ValueError):
        raise HTTPException(status_code=422, detail="latitude and longitude (floats) are required")
    return await ctrl.update_event_gps(event_id, lat, lng, current_user, db)


