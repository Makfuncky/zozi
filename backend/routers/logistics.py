"""
Logistics Router — shipping carriers, zones, and shipment fulfilment.
All business logic lives in controllers/logistics_controller.py.
"""
from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.database import get_db
from routers.auth import get_current_user
import controllers.logistics_controller as ctrl

router = APIRouter()


# ── Summary ────────────────────────────────────────────────────────────────────

@router.get("/summary")
async def get_logistics_summary(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await ctrl.get_logistics_summary(current_user, db)


# ── Carriers ──────────────────────────────────────────────────────────────────

@router.get("/carriers")
async def get_carriers(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await ctrl.get_carriers(current_user, db)


@router.post("/carriers")
async def create_carrier(
    data: dict[str, Any],
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await ctrl.create_carrier(data, current_user, db)


@router.delete("/carriers/{carrier_id}")
async def delete_carrier(
    carrier_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await ctrl.delete_carrier(carrier_id, current_user, db)


# ── Shipping Zones ────────────────────────────────────────────────────────────

@router.get("/zones")
async def get_shipping_zones(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await ctrl.get_shipping_zones(current_user, db)


@router.post("/zones")
async def upsert_shipping_zone(
    data: dict[str, Any],
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await ctrl.upsert_shipping_zone(data, current_user, db)


@router.put("/zones/{zone_id}")
async def update_shipping_zone(
    zone_id: int,
    data: dict[str, Any],
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    data["id"] = zone_id
    return await ctrl.upsert_shipping_zone(data, current_user, db)


@router.delete("/zones/{zone_id}")
async def delete_shipping_zone(
    zone_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await ctrl.delete_shipping_zone(zone_id, current_user, db)


# ── Orders to Fulfil ──────────────────────────────────────────────────────────

@router.get("/orders/pending")
async def get_orders_to_fulfil(
    limit: int = 200,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await ctrl.get_orders_to_fulfil(current_user, db, limit=limit, offset=offset)


# ── Shipments ─────────────────────────────────────────────────────────────────

@router.post("/shipments")
async def create_shipment(
    data: dict[str, Any],
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await ctrl.create_shipment(data, current_user, db)


@router.get("/shipments/scan")
async def scan_lookup_shipment(
    code: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Look up a shipment by tracking number or scan code. Admin only."""
    if str(current_user.get("role") or "").lower() not in ("admin", "sub_admin", "moderator", "support"):
        raise HTTPException(status_code=403, detail="Admin access required")
    from models import Shipment
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


@router.put("/shipments/{shipment_id}/status")
async def admin_update_shipment_status(
    shipment_id: int,
    data: dict[str, Any],
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Admin endpoint to update a shipment status directly (bypasses supplier check)."""
    if str(current_user.get("role") or "").lower() not in ("admin", "sub_admin", "moderator", "support"):
        raise HTTPException(status_code=403, detail="Admin access required")
    from models import Shipment, ShipmentEvent
    from datetime import datetime, timezone
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


@router.get("/shipments/active")
async def get_active_shipments(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await ctrl.get_active_shipments(current_user, db)


@router.get("/shipments/history")
async def get_shipment_history(
    page: int = 1,
    per_page: int = 30,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await ctrl.get_shipment_history(current_user, db, page=page, per_page=per_page)


@router.get("/shipments/{shipment_id}/events")
async def get_shipment_events(
    shipment_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await ctrl.get_shipment_events(shipment_id, current_user, db)


@router.post("/shipments/{shipment_id}/scan")
async def scan_shipment_event(
    shipment_id: int,
    data: dict[str, Any],
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await ctrl.scan_shipment_event(shipment_id, data, current_user, db)


@router.patch("/shipments/{shipment_id}")
async def update_shipment_status(
    shipment_id: int,
    data: dict[str, Any],
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await ctrl.update_shipment_status(shipment_id, data, current_user, db)


@router.get("/distribution/channels")
async def get_distribution_channels(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await ctrl.get_distribution_channels(current_user, db)


# ── GPS Event Update ─────────────────────────────────────────────────────────

@router.patch("/events/{event_id}/gps")
async def update_shipment_event_gps(
    event_id: int,
    data: dict[str, Any],
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Attach GPS coordinates to a shipment event (supplier or admin).

    Body: ``{"latitude": float, "longitude": float}``
    """
    try:
        lat = float(data["latitude"])
        lng = float(data["longitude"])
    except (KeyError, TypeError, ValueError):
        raise HTTPException(status_code=422, detail="latitude and longitude (floats) are required")
    return await ctrl.update_event_gps(event_id, lat, lng, current_user, db)

