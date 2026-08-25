"""Logistics logistics router — consolidated from 12 source files."""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status


router = APIRouter(prefix="/api/v1/logistics/logistics", tags=["logistics", "logistics"])


# === From logistics_health.py ===
"""
Logistics Health API Endpoints
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from rbac import get_current_user
from infrastructure.database.database import get_db
from domains.logistics.services.health.service import get_logistics_health_engine


@router.get("/health/logistics/{partner_id}")
def get_logistics_health(
    partner_id: int,
    country_code: str = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    engine = get_logistics_health_engine(db)
    return engine.calculate_health_score(partner_id, country_code)


@router.get("/health/logistics")
def list_logistics_health(
    country_code: str = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from domains.logistics.models.logistics_entities import LogisticsPartner
    from domains.logistics.models.logistics_entities import LogisticsPartnerProfile
    profiles = db.query(LogisticsPartnerProfile).all()
    results = []
    for p in profiles:
        engine = get_logistics_health_engine(db)
        health = engine.calculate_health_score(p.id, country_code)
        partner = db.query(LogisticsPartner).filter(LogisticsPartner.id == p.partner_id).first()
        health["profile"] = {
            "name": partner.name if partner else None,
            "rating": 0,
        }
        results.append(health)
    results.sort(key=lambda x: x.get("trust_score", 0), reverse=True)
    return {"logistics_partners": results[:50]}


# === From logistics_health_list.py ===
"""
Logistics Health API Endpoints
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from infrastructure.database.database import get_db
from rbac import get_current_user
from domains.logistics.services.health.service import get_logistics_health_engine


@router.get("/health/logistics/{partner_id}")
def get_logistics_health(
    partner_id: int,
    country_code: str = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    engine = get_logistics_health_engine(db)
    return engine.calculate_health_score(partner_id, country_code)


@router.get("/health/logistics")
def list_logistics_health(
    country_code: str = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from domains.logistics.models.logistics_entities import LogisticsPartnerProfile
    from domains.logistics.models.logistics_entities import LogisticsPartner
    profiles = db.query(LogisticsPartnerProfile).all()
    results = []
    for p in profiles:
        engine = get_logistics_health_engine(db)
        health = engine.calculate_health_score(p.id, country_code)
        partner = db.query(LogisticsPartner).filter(LogisticsPartner.id == p.partner_id).first()
        health["profile"] = {
            "name": partner.name if partner else None,
            "rating": 0,
        }
        results.append(health)
    results.sort(key=lambda x: x.get("trust_score", 0), reverse=True)
    return {"logistics_partners": results[:50]}


# === From logistics_locations.py ===
"""
Logistics Partner Location Router
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from rbac import get_current_user
from infrastructure.database.database import get_db
from domains.country.models.countries import CountryConfig
from domains.country.models.country_control import LogisticsPartnerLocation
from domains.logistics.models.logistics_entities import LogisticsPartner

logger = logging.getLogger(__name__)


@router.get("/{country_code}/locations/logistics-partners", response_model=List[dict])
def list_logistics_partner_locations(
    country_code: str = Path(...),
    partner_id: Optional[int] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    query = db.query(LogisticsPartnerLocation).filter(
        LogisticsPartnerLocation.country_code == country_code.upper()
    )
    if partner_id is not None:
        query = query.filter(LogisticsPartnerLocation.partner_id == partner_id)
    if is_active is not None:
        query = query.filter(LogisticsPartnerLocation.is_active == is_active)
    locations = query.order_by(LogisticsPartnerLocation.location_type, LogisticsPartnerLocation.created_at).all()
    return [
        {
            "id": loc.id,
            "partner_id": loc.partner_id,
            "location_type": loc.location_type,
            "latitude": loc.latitude,
            "longitude": loc.longitude,
            "address": loc.address,
            "is_active": loc.is_active,
            "created_at": loc.created_at,
        }
        for loc in locations
    ]


@router.post("/{country_code}/locations/logistics-partners", response_model=dict)
def create_logistics_partner_location(
    country_code: str = Path(...),
    payload: dict = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if not payload:
        payload = {}
    config = db.query(CountryConfig).filter(CountryConfig.code == country_code.upper()).first()
    if not config:
        raise HTTPException(status_code=404, detail="Country not found")
    
    partner_id = payload.get("partner_id")
    if not partner_id:
        raise HTTPException(status_code=422, detail="partner_id is required")
    
    partner = db.query(LogisticsPartner).filter(LogisticsPartner.id == partner_id).first()
    if not partner:
        raise HTTPException(status_code=404, detail="Logistics partner not found")
    
    location = LogisticsPartnerLocation(
        country_code=country_code.upper(),
        partner_id=partner_id,
        location_type=payload.get("location_type", "warehouse"),
        latitude=payload.get("latitude"),
        longitude=payload.get("longitude"),
        address=payload.get("address"),
        is_active=payload.get("is_active", True),
    )
    db.add(location)
    db.commit()
    db.refresh(location)
    return {"id": location.id, "message": "Logistics partner location created"}


# === From logistics_locations_create.py ===
"""
Logistics Partner Location Router
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from infrastructure.database.database import get_db
from domains.country.models.countries import CountryConfig
from domains.country.models.country_control import LogisticsPartnerLocation
from domains.logistics.models.logistics_entities import LogisticsPartner
from rbac import get_current_user

logger = logging.getLogger(__name__)


@router.get("/{country_code}/locations/logistics-partners", response_model=List[dict])
def list_logistics_partner_locations(
    country_code: str = Path(...),
    partner_id: Optional[int] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    query = db.query(LogisticsPartnerLocation).filter(
        LogisticsPartnerLocation.country_code == country_code.upper()
    )
    if partner_id is not None:
        query = query.filter(LogisticsPartnerLocation.partner_id == partner_id)
    if is_active is not None:
        query = query.filter(LogisticsPartnerLocation.is_active == is_active)
    locations = query.order_by(LogisticsPartnerLocation.location_type, LogisticsPartnerLocation.created_at).all()
    return [
        {
            "id": loc.id,
            "partner_id": loc.partner_id,
            "location_type": loc.location_type,
            "latitude": loc.latitude,
            "longitude": loc.longitude,
            "address": loc.address,
            "is_active": loc.is_active,
            "created_at": loc.created_at,
        }
        for loc in locations
    ]


@router.post("/{country_code}/locations/logistics-partners", response_model=dict)
def create_logistics_partner_location(
    country_code: str = Path(...),
    payload: dict = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if not payload:
        payload = {}
    config = db.query(CountryConfig).filter(CountryConfig.code == country_code.upper()).first()
    if not config:
        raise HTTPException(status_code=404, detail="Country not found")
    
    partner_id = payload.get("partner_id")
    if not partner_id:
        raise HTTPException(status_code=422, detail="partner_id is required")
    
    partner = db.query(LogisticsPartner).filter(LogisticsPartner.id == partner_id).first()
    if not partner:
        raise HTTPException(status_code=404, detail="Logistics partner not found")
    
    location = LogisticsPartnerLocation(
        country_code=country_code.upper(),
        partner_id=partner_id,
        location_type=payload.get("location_type", "warehouse"),
        latitude=payload.get("latitude"),
        longitude=payload.get("longitude"),
        address=payload.get("address"),
        is_active=payload.get("is_active", True),
    )
    db.add(location)
    db.commit()
    db.refresh(location)
    return {"id": location.id, "message": "Logistics partner location created"}


# === From logistics_logistics_status.py ===
"""
Logistics Router — shipping carriers, zones, and shipment fulfilment.
All business logic lives in controllers/logistics_controller.py.
"""
from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from infrastructure.database.database import get_db
from modules.admin.routers.core_auth_routes import get_current_user
import domains.orders.services.logistics_controller as ctrl


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
    from domains.logistics.models.logistics_entities import Shipment
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
    from domains.logistics.models.logistics_entities import Shipment
    from domains.logistics.models.logistics_entities import ShipmentEvent
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


# === From logistics_orders_list.py ===
"""Logistics partner orders router."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from infrastructure.database.database import get_db
from domains.governance.models.user import User
from domains.logistics.models.logistics_entities import Shipment
from domains.logistics.models.logistics_entities import LogisticsPartner
from infrastructure.utils.dependencies import require_logistics


@router.get("")
def list_assigned_shipments(current_user: User = Depends(require_logistics), db: Session = Depends(get_db)):
    partner = db.query(LogisticsPartner).filter(LogisticsPartner.user_id == current_user.id).first()
    if not partner: raise HTTPException(404)
    shipments = db.query(Shipment).filter(Shipment.assigned_partner_id == partner.id).all()
    return [{
        "id": s.id,
        "order_id": s.order_id,
        "status": s.status,
        "tracking_number": s.tracking_number,
        "carrier_name": s.carrier_name,
        "distribution_channel": s.distribution_channel,
        "estimated_delivery": s.estimated_delivery.isoformat() if s.estimated_delivery else None,
        "actual_delivery": s.actual_delivery.isoformat() if s.actual_delivery else None,
    } for s in shipments]


# === From logistics_orders_v2.py ===
"""
Logistics Partner Order Management Router — full lifecycle.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from infrastructure.database.database import get_db
from domains.governance.models.user import User
from domains.logistics.models.logistics_entities import LogisticsPartner
from domains.logistics.models.logistics_entities import Shipment
from infrastructure.utils.dependencies import require_logistics, require_admin
from domains.orders.services.tracking.service import get_available_orders_for_logistics
from domains.orders.services.tracking.service import get_order_shipment_label
from domains.orders.services.tracking.service import logistics_confirm_pickup
from domains.orders.services.tracking.service import logistics_scan_and_receive
from domains.orders.services.tracking.service import logistics_update_transit_status
from domains.orders.services.tracking.service import logistics_deliver_order
from domains.orders.services.tracking.service import logistics_cancel_pickup

logger = logging.getLogger(__name__)


# ── Pydantic schemas for POST bodies ───────────────────────────────

class ScanReceiveRequest(BaseModel):
    scan_code: str
    location: Optional[str] = None

class UpdateTransitRequest(BaseModel):
    event_type: str  # logistics_received, distribution_checkpoint, out_for_delivery, shipment_delayed, shipment_failed, shipment_rescheduled, shipment_cancelled, shipment_returned
    location: Optional[str] = None
    notes: Optional[str] = None

class DeliverRequest(BaseModel):
    signature_name: Optional[str] = None
    signature_data_url: Optional[str] = None
    notes: Optional[str] = None

class CancelPickupRequest(BaseModel):
    reason: Optional[str] = None


# ── Endpoints ──────────────────────────────────────────────────────

@router.get("/available")
def list_available_orders(
    current_user: User = Depends(require_logistics),
    db: Session = Depends(get_db),
):
    """List all orders in 'prepared' status available for pickup."""
    return get_available_orders_for_logistics(db)


@router.get("/my")
def list_my_pickups(
    current_user: User = Depends(require_logistics),
    db: Session = Depends(get_db),
):
    """List shipments assigned to this logistics partner."""
    partner = db.query(LogisticsPartner).filter(
        LogisticsPartner.user_id == current_user.id
    ).first()
    if not partner:
        raise HTTPException(404, "Logistics partner profile not found")
    shipments = (
        db.query(Shipment)
        .filter(Shipment.assigned_partner_id == partner.id)
        .order_by(Shipment.updated_at.desc())
        .all()
    )
    return [
        {
            "id": s.id, "order_id": s.order_id, "status": s.status,
            "tracking_number": s.tracking_number, "scan_code": s.scan_code,
            "current_hub": s.current_hub,
            "package_weight_kg": float(s.package_weight_kg) if s.package_weight_kg else None,
            "packaged_at": s.packaged_at.isoformat() if s.packaged_at else None,
            "shipped_at": s.shipped_at.isoformat() if s.shipped_at else None,
            "estimated_delivery": s.estimated_delivery.isoformat() if s.estimated_delivery else None,
            "actual_delivery": s.actual_delivery.isoformat() if s.actual_delivery else None,
            "delivery_signature_name": s.delivery_signature_name,
            "updated_at": s.updated_at.isoformat() if s.updated_at else None,
        }
        for s in shipments
    ]


@router.post("/{order_id}/confirm-pickup")
def confirm_pickup(
    order_id: int,
    current_user: User = Depends(require_logistics),
    db: Session = Depends(get_db),
):
    """Confirm pickup — marks order as 'picking_up' and removes from other logistics lists."""
    result = logistics_confirm_pickup(db, order_id, current_user.id)
    if not result["success"]:
        raise HTTPException(400, result["error"])
    return result


@router.post("/{order_id}/scan-receive")
def scan_and_receive(
    order_id: int,
    body: ScanReceiveRequest,
    current_user: User = Depends(require_logistics),
    db: Session = Depends(get_db),
):
    """Scan QR code and receive package from supplier. Status → shipped/picked_from_supplier."""
    result = logistics_scan_and_receive(db, order_id, current_user.id, body.scan_code, body.location)
    if not result["success"]:
        raise HTTPException(400, result["error"])
    return result


@router.post("/{order_id}/update-transit")
def update_transit(
    order_id: int,
    body: UpdateTransitRequest,
    current_user: User = Depends(require_logistics),
    db: Session = Depends(get_db),
):
    """Update transit sub-status. Valid types:
    logistics_received, distribution_checkpoint, out_for_delivery,
    shipment_delayed, shipment_failed, shipment_rescheduled,
    shipment_cancelled, shipment_returned"""
    result = logistics_update_transit_status(db, order_id, current_user.id,
                                              body.event_type, body.location, body.notes)
    if not result["success"]:
        raise HTTPException(400, result["error"])
    return result


@router.post("/{order_id}/deliver")
def deliver_order(
    order_id: int,
    body: DeliverRequest,
    current_user: User = Depends(require_logistics),
    db: Session = Depends(get_db),
):
    """Deliver order to customer with optional e-signature."""
    result = logistics_deliver_order(db, order_id, current_user.id,
                                      body.signature_name, body.signature_data_url, body.notes)
    if not result["success"]:
        raise HTTPException(400, result["error"])
    return result


@router.post("/{order_id}/cancel-pickup")
def cancel_pickup(
    order_id: int,
    body: CancelPickupRequest = CancelPickupRequest(),
    current_user: User = Depends(require_logistics),
    db: Session = Depends(get_db),
):
    """Cancel pickup before shipped status. Order returns to 'prepared'."""
    result = logistics_cancel_pickup(db, order_id, current_user.id, body.reason)
    if not result["success"]:
        raise HTTPException(400, result["error"])
    return result


@router.get("/{order_id}/label")
def get_label(
    order_id: int,
    current_user: User = Depends(require_logistics),
    db: Session = Depends(get_db),
):
    """Get packing label data for printing (includes QR code, customer info, lat/lng)."""
    label = get_order_shipment_label(order_id, db)
    if not label:
        raise HTTPException(404, "Order not found")
    return label


# === From logistics_partner.py ===
"""
Logistics Partner Router — partner management and partner dashboard.
All business logic in controllers/logistics_partner_controller.py.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

import domains.orders.services.logistics_partner_controller as ctrl
from infrastructure.database.database import get_db
from modules.admin.routers.auth import get_current_user


@router.get("/public")
def list_public_logistics_partners(
    request: Request,
    q: Optional[str] = Query(None),
    country: Optional[str] = Query(None, min_length=2, max_length=10),
    limit: int = Query(12, ge=1, le=50),
    db: Session = Depends(get_db),
):
    resolved_country = (
        country
        or request.headers.get("X-Country-Code")
        or getattr(request.state, "country_code", None)
    )
    return ctrl.list_public_partners(db, q=q, country=resolved_country, limit=limit)


@router.get("/public/{partner_id}")
def get_public_logistics_partner(
    partner_id: int,
    db: Session = Depends(get_db),
):
    return ctrl.get_public_partner(partner_id, db)


@router.get("/profile")
def get_partner_profile(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.get_my_partner_profile(current_user, db)


@router.put("/profile")
def update_partner_profile(
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.update_my_partner_profile(data, current_user, db)


@router.post("/profile/terms/accept")
def accept_partner_profile_terms(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.accept_partner_terms(current_user, db)


@router.post("/profile/submit-review")
def submit_partner_profile_review(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.submit_partner_profile_for_review(current_user, db)


@router.get("/service-areas")
def get_partner_service_areas(
    partner_id: Optional[int] = Query(None),
    approval_status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.list_my_partner_service_areas(
        current_user,
        db,
        partner_id=partner_id,
        approval_status=approval_status,
    )


@router.get("/pricing-profiles")
def get_partner_pricing_profiles(
    partner_id: Optional[int] = Query(None),
    approval_status: Optional[str] = Query(None),
    service_area_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.list_my_partner_pricing_profiles(
        current_user,
        db,
        partner_id=partner_id,
        approval_status=approval_status,
        service_area_id=service_area_id,
    )


@router.get("/category-rules")
def get_partner_category_rules(
    partner_id: Optional[int] = Query(None),
    approval_status: Optional[str] = Query(None),
    service_area_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.list_my_partner_category_rules(
        current_user,
        db,
        partner_id=partner_id,
        approval_status=approval_status,
        service_area_id=service_area_id,
    )


@router.get("/vehicle-rules")
def get_partner_vehicle_rules(
    partner_id: Optional[int] = Query(None),
    approval_status: Optional[str] = Query(None),
    service_area_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.list_my_partner_vehicle_rules(
        current_user,
        db,
        partner_id=partner_id,
        approval_status=approval_status,
        service_area_id=service_area_id,
    )


@router.get("/pricing-insights")
def get_partner_pricing_insights(
    partner_id: Optional[int] = Query(None),
    service_area_id: Optional[int] = Query(None),
    limit: int = Query(12, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.get_partner_pricing_insights(
        current_user,
        db,
        partner_id=partner_id,
        service_area_id=service_area_id,
        limit=limit,
    )


@router.post("/pricing-profiles")
def create_partner_pricing_profile(
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.upsert_my_partner_pricing_profile(None, data, current_user, db)


@router.put("/pricing-profiles/{profile_id}")
def update_partner_pricing_profile(
    profile_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.upsert_my_partner_pricing_profile(profile_id, data, current_user, db)


@router.delete("/pricing-profiles/{profile_id}")
def delete_partner_pricing_profile(
    profile_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.delete_my_partner_pricing_profile(profile_id, current_user, db)


@router.post("/category-rules")
def create_partner_category_rule(
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.upsert_my_partner_category_rule(None, data, current_user, db)


@router.put("/category-rules/{rule_id}")
def update_partner_category_rule(
    rule_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.upsert_my_partner_category_rule(rule_id, data, current_user, db)


@router.delete("/category-rules/{rule_id}")
def delete_partner_category_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.delete_my_partner_category_rule(rule_id, current_user, db)


@router.post("/vehicle-rules")
def create_partner_vehicle_rule(
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.upsert_my_partner_vehicle_rule(None, data, current_user, db)


@router.put("/vehicle-rules/{rule_id}")
def update_partner_vehicle_rule(
    rule_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.upsert_my_partner_vehicle_rule(rule_id, data, current_user, db)


@router.delete("/vehicle-rules/{rule_id}")
def delete_partner_vehicle_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.delete_my_partner_vehicle_rule(rule_id, current_user, db)


@router.post("/service-areas")
def create_partner_service_area(
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.upsert_my_partner_service_area(None, data, current_user, db)


@router.put("/service-areas/{area_id}")
def update_partner_service_area(
    area_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.upsert_my_partner_service_area(area_id, data, current_user, db)


@router.delete("/service-areas/{area_id}")
def delete_partner_service_area(
    area_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.delete_my_partner_service_area(area_id, current_user, db)


@router.post("/review/profile/{partner_id}")
def review_logistics_partner_profile(
    partner_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.review_partner_profile(partner_id, data, current_user, db)


@router.post("/review/service-areas/{area_id}")
def review_logistics_partner_service_area(
    area_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.review_partner_service_area(area_id, data, current_user, db)


@router.post("/review/pricing-profiles/{profile_id}")
def review_logistics_partner_pricing_profile(
    profile_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.review_partner_pricing_profile(profile_id, data, current_user, db)


@router.post("/review/category-rules/{rule_id}")
def review_logistics_partner_category_rule(
    rule_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.review_partner_category_rule(rule_id, data, current_user, db)


@router.post("/review/vehicle-rules/{rule_id}")
def review_logistics_partner_vehicle_rule(
    rule_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.review_partner_vehicle_rule(rule_id, data, current_user, db)


@router.post("/shipping-quote")
def get_logistics_shipping_quote(
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.shipping_quote_for_customer(data, db)


# ── Admin: manage partners ────────────────────────────────────────────────────

@router.get("/")
def list_partners(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Admin: list all logistics partners."""
    return ctrl.list_partners(current_user, db)


@router.post("/", status_code=201)
def create_partner(
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Admin: onboard a new logistics partner."""
    return ctrl.create_partner(data, current_user, db)


class BulkPartnerAdminActionRequest(BaseModel):
    partner_ids: List[int]
    action: str
    note: str | None = None


@router.post("/bulk")
def bulk_manage_logistics_partners(
    body: BulkPartnerAdminActionRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Admin bulk actions for logistics partner review and portal lifecycle."""
    return ctrl.bulk_manage_partners(body.partner_ids, body.action, body.note, current_user, db)


@router.put("/{partner_id}")
def update_partner(
    partner_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Admin: update partner details or status."""
    return ctrl.update_partner(partner_id, data, current_user, db)


@router.delete("/{partner_id}")
def delete_partner(
    partner_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Admin-only: remove a logistics partner."""
    return ctrl.delete_partner(partner_id, current_user, db)


# ── Partner Dashboard ─────────────────────────────────────────────────────────

@router.get("/dashboard")
def partner_dashboard(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Dashboard stats for logistics partner or admin."""
    return ctrl.get_partner_dashboard(current_user, db)


@router.get("/analytics")
def partner_analytics(
    period: str = Query("30d", description="Analytics lookback window: 7d, 30d, or 90d"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.get_partner_analytics(current_user, db, period=period)


@router.get("/payouts")
def partner_payouts(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.get_partner_payouts(current_user, db)


@router.post("/payouts/request")
def request_payout(
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.request_partner_payout(data, current_user, db)


@router.get("/payouts/pending")
def pending_payouts(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.list_pending_partner_payouts(current_user, db)


@router.post("/payouts/{payout_id}/verify")
def verify_payout(
    payout_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.verify_partner_payout(payout_id, data, current_user, db)


@router.get("/shipments/scan")
def scan_lookup_shipment(
    code: str = Query(..., description="Scan code or tracking number to look up"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Look up a shipment by scan code or tracking number (logistics partners and admins)."""
    return ctrl.scan_lookup_shipment_partner(code, current_user, db)


@router.get("/shipments")
def list_partner_shipments(
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List shipments assigned to (or visible by) this logistics partner."""
    return ctrl.get_partner_shipments(current_user, db, status=status, page=page, page_size=page_size)


@router.put("/shipments/{shipment_id}/status")
def update_shipment_status(
    shipment_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Partner updates the status of a shipment (e.g., in_transit, delivered)."""
    return ctrl.update_shipment_status_partner(shipment_id, data, current_user, db)


@router.post("/shipments/{shipment_id}/confirmation-request")
def create_shipment_confirmation_request(
    shipment_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Partner creates a pending pickup or delivery confirmation request."""
    return ctrl.create_shipment_confirmation_request_partner(shipment_id, data, current_user, db)


class BulkShipmentStatusRequest(BaseModel):
    shipment_ids: List[int]
    status: str
    notes: str | None = None


@router.put("/shipments/bulk-status")
def bulk_update_shipments_status(
    body: BulkShipmentStatusRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Bulk-update shipment status for multiple shipments (up to 100).
    Partners can only update their own assigned shipments.
    Note: 'delivered' requires signature — use the single-shipment endpoint instead.
    """
    return ctrl.bulk_update_shipment_status_partner(
        body.shipment_ids, body.status, body.notes, current_user, db
    )


# ── Logistics Partner Bank Account (Payout Beneficiary) ───────────────────────

@router.get("/me/bank-account")
def get_partner_bank_account(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get the logistics partner's saved payout bank account."""
    return ctrl.get_partner_bank_account(current_user, db)


@router.put("/me/bank-account")
def upsert_partner_bank_account(
    body: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Submit or update the logistics partner's payout bank account. Triggers admin verification."""
    return ctrl.upsert_partner_bank_account(body, current_user, db)


@router.get("/me/cod-remittance-receipts")
def list_my_cod_remittance_receipts(
    status: Optional[str] = Query(None),
    settlement_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.list_partner_cod_remittance_receipts(current_user, db, status=status, settlement_id=settlement_id)


@router.post("/me/cod-remittance-receipts", status_code=201)
async def upload_my_cod_remittance_receipt(
    settlement_id: int = Form(...),
    amount: float = Form(...),
    bank_reference: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await ctrl.upload_partner_cod_remittance_receipt(
        settlement_id,
        amount,
        file,
        bank_reference,
        notes,
        current_user,
        db,
    )


# ── Logistics Partner Documents ───────────────────────────────────────────────

@router.get("/me/docs")
def list_lp_documents(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List all KYC/compliance documents submitted by the authenticated logistics partner."""
    return ctrl.list_partner_documents(current_user, db)


@router.post("/me/docs/upload")
async def upload_lp_document(
    file: UploadFile = File(...),
    document_type: str = Form(...),
    document_name: str = Form(""),
    expires_at: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Upload a KYC/compliance document (multipart/form-data)."""
    return await ctrl.upload_partner_document(file, document_type, document_name, expires_at, current_user, db)


@router.delete("/me/docs/{doc_id}")
def delete_lp_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Delete a pending or rejected document."""
    return ctrl.delete_partner_document(doc_id, current_user, db)


@router.post("/admin/docs/{doc_id}/review")
def admin_review_lp_document(
    doc_id: int,
    body: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Admin reviews a logistics partner document — approve/reject."""
    return ctrl.admin_review_lp_document(doc_id, body, current_user, db)


# ── City Distance Matrix (admin only) ─────────────────────────────────────────

@router.get("/city-distances")
def list_city_distances(
    origin_country_code: Optional[str] = Query(None),
    destination_country_code: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Admin: list city distance matrix entries with optional filtering."""
    return ctrl.list_city_distances(current_user, db, origin_country_code=origin_country_code, destination_country_code=destination_country_code, q=q, page=page, page_size=page_size)


@router.post("/city-distances")
def create_city_distance(
    body: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Admin: create a new city distance matrix entry."""
    return ctrl.create_city_distance(body, current_user, db)


@router.put("/city-distances/{matrix_id}")
def update_city_distance(
    matrix_id: int,
    body: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Admin: update distance_km (and optional notes) for an existing entry."""
    return ctrl.update_city_distance(matrix_id, body, current_user, db)


@router.delete("/city-distances/{matrix_id}")
def delete_city_distance(
    matrix_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Admin: delete a city distance matrix entry."""
    return ctrl.delete_city_distance(matrix_id, current_user, db)


# === From logistics_partner_verify.py ===
"""
Logistics Partner Router — partner management and partner dashboard.
All business logic in controllers/logistics_partner_controller.py.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from infrastructure.database.database import get_db
from modules.admin.routers.core_auth_routes import get_current_user
import domains.orders.services.logistics_partner_controller as ctrl


@router.get("/public")
def list_public_logistics_partners(
    request: Request,
    q: Optional[str] = Query(None),
    country: Optional[str] = Query(None, min_length=2, max_length=10),
    limit: int = Query(12, ge=1, le=50),
    db: Session = Depends(get_db),
):
    resolved_country = (
        country
        or request.headers.get("X-Country-Code")
        or getattr(request.state, "country_code", None)
    )
    return ctrl.list_public_partners(db, q=q, country=resolved_country, limit=limit)


@router.get("/public/{partner_id}")
def get_public_logistics_partner(
    partner_id: int,
    db: Session = Depends(get_db),
):
    return ctrl.get_public_partner(partner_id, db)


@router.get("/profile")
def get_partner_profile(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.get_my_partner_profile(current_user, db)


@router.put("/profile")
def update_partner_profile(
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.update_my_partner_profile(data, current_user, db)


@router.post("/profile/terms/accept")
def accept_partner_profile_terms(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.accept_partner_terms(current_user, db)


@router.post("/profile/submit-review")
def submit_partner_profile_review(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.submit_partner_profile_for_review(current_user, db)


@router.get("/service-areas")
def get_partner_service_areas(
    partner_id: Optional[int] = Query(None),
    approval_status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.list_my_partner_service_areas(
        current_user,
        db,
        partner_id=partner_id,
        approval_status=approval_status,
    )


@router.get("/pricing-profiles")
def get_partner_pricing_profiles(
    partner_id: Optional[int] = Query(None),
    approval_status: Optional[str] = Query(None),
    service_area_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.list_my_partner_pricing_profiles(
        current_user,
        db,
        partner_id=partner_id,
        approval_status=approval_status,
        service_area_id=service_area_id,
    )


@router.get("/category-rules")
def get_partner_category_rules(
    partner_id: Optional[int] = Query(None),
    approval_status: Optional[str] = Query(None),
    service_area_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.list_my_partner_category_rules(
        current_user,
        db,
        partner_id=partner_id,
        approval_status=approval_status,
        service_area_id=service_area_id,
    )


@router.get("/vehicle-rules")
def get_partner_vehicle_rules(
    partner_id: Optional[int] = Query(None),
    approval_status: Optional[str] = Query(None),
    service_area_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.list_my_partner_vehicle_rules(
        current_user,
        db,
        partner_id=partner_id,
        approval_status=approval_status,
        service_area_id=service_area_id,
    )


@router.get("/pricing-insights")
def get_partner_pricing_insights(
    partner_id: Optional[int] = Query(None),
    service_area_id: Optional[int] = Query(None),
    limit: int = Query(12, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.get_partner_pricing_insights(
        current_user,
        db,
        partner_id=partner_id,
        service_area_id=service_area_id,
        limit=limit,
    )


@router.post("/pricing-profiles")
def create_partner_pricing_profile(
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.upsert_my_partner_pricing_profile(None, data, current_user, db)


@router.put("/pricing-profiles/{profile_id}")
def update_partner_pricing_profile(
    profile_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.upsert_my_partner_pricing_profile(profile_id, data, current_user, db)


@router.delete("/pricing-profiles/{profile_id}")
def delete_partner_pricing_profile(
    profile_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.delete_my_partner_pricing_profile(profile_id, current_user, db)


@router.post("/category-rules")
def create_partner_category_rule(
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.upsert_my_partner_category_rule(None, data, current_user, db)


@router.put("/category-rules/{rule_id}")
def update_partner_category_rule(
    rule_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.upsert_my_partner_category_rule(rule_id, data, current_user, db)


@router.delete("/category-rules/{rule_id}")
def delete_partner_category_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.delete_my_partner_category_rule(rule_id, current_user, db)


@router.post("/vehicle-rules")
def create_partner_vehicle_rule(
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.upsert_my_partner_vehicle_rule(None, data, current_user, db)


@router.put("/vehicle-rules/{rule_id}")
def update_partner_vehicle_rule(
    rule_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.upsert_my_partner_vehicle_rule(rule_id, data, current_user, db)


@router.delete("/vehicle-rules/{rule_id}")
def delete_partner_vehicle_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.delete_my_partner_vehicle_rule(rule_id, current_user, db)


@router.post("/service-areas")
def create_partner_service_area(
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.upsert_my_partner_service_area(None, data, current_user, db)


@router.put("/service-areas/{area_id}")
def update_partner_service_area(
    area_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.upsert_my_partner_service_area(area_id, data, current_user, db)


@router.delete("/service-areas/{area_id}")
def delete_partner_service_area(
    area_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.delete_my_partner_service_area(area_id, current_user, db)


@router.post("/review/profile/{partner_id}")
def review_logistics_partner_profile(
    partner_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.review_partner_profile(partner_id, data, current_user, db)


@router.post("/review/service-areas/{area_id}")
def review_logistics_partner_service_area(
    area_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.review_partner_service_area(area_id, data, current_user, db)


@router.post("/review/pricing-profiles/{profile_id}")
def review_logistics_partner_pricing_profile(
    profile_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.review_partner_pricing_profile(profile_id, data, current_user, db)


@router.post("/review/category-rules/{rule_id}")
def review_logistics_partner_category_rule(
    rule_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.review_partner_category_rule(rule_id, data, current_user, db)


@router.post("/review/vehicle-rules/{rule_id}")
def review_logistics_partner_vehicle_rule(
    rule_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.review_partner_vehicle_rule(rule_id, data, current_user, db)


@router.post("/shipping-quote")
def get_logistics_shipping_quote(
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.shipping_quote_for_customer(data, db)


# ── Admin: manage partners ────────────────────────────────────────────────────

@router.get("/")
def list_partners(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Admin: list all logistics partners."""
    return ctrl.list_partners(current_user, db)


@router.post("/", status_code=201)
def create_partner(
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Admin: onboard a new logistics partner."""
    return ctrl.create_partner(data, current_user, db)


class BulkPartnerAdminActionRequest(BaseModel):
    partner_ids: List[int]
    action: str
    note: str | None = None


@router.post("/bulk")
def bulk_manage_logistics_partners(
    body: BulkPartnerAdminActionRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Admin bulk actions for logistics partner review and portal lifecycle."""
    return ctrl.bulk_manage_partners(body.partner_ids, body.action, body.note, current_user, db)


@router.put("/{partner_id}")
def update_partner(
    partner_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Admin: update partner details or status."""
    return ctrl.update_partner(partner_id, data, current_user, db)


@router.delete("/{partner_id}")
def delete_partner(
    partner_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Admin-only: remove a logistics partner."""
    return ctrl.delete_partner(partner_id, current_user, db)


# ── Partner Dashboard ─────────────────────────────────────────────────────────

@router.get("/dashboard")
def partner_dashboard(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Dashboard stats for logistics partner or admin."""
    return ctrl.get_partner_dashboard(current_user, db)


@router.get("/analytics")
def partner_analytics(
    period: str = Query("30d", description="Analytics lookback window: 7d, 30d, or 90d"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.get_partner_analytics(current_user, db, period=period)


@router.get("/payouts")
def partner_payouts(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.get_partner_payouts(current_user, db)


@router.post("/payouts/request")
def request_payout(
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.request_partner_payout(data, current_user, db)


@router.get("/payouts/pending")
def pending_payouts(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.list_pending_partner_payouts(current_user, db)


@router.post("/payouts/{payout_id}/verify")
def verify_payout(
    payout_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.verify_partner_payout(payout_id, data, current_user, db)


@router.get("/shipments/scan")
def scan_lookup_shipment(
    code: str = Query(..., description="Scan code or tracking number to look up"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Look up a shipment by scan code or tracking number (logistics partners and admins)."""
    return ctrl.scan_lookup_shipment_partner(code, current_user, db)


@router.get("/shipments")
def list_partner_shipments(
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List shipments assigned to (or visible by) this logistics partner."""
    return ctrl.get_partner_shipments(current_user, db, status=status, page=page, page_size=page_size)


@router.put("/shipments/{shipment_id}/status")
def update_shipment_status(
    shipment_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Partner updates the status of a shipment (e.g., in_transit, delivered)."""
    return ctrl.update_shipment_status_partner(shipment_id, data, current_user, db)


@router.post("/shipments/{shipment_id}/confirmation-request")
def create_shipment_confirmation_request(
    shipment_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Partner creates a pending pickup or delivery confirmation request."""
    return ctrl.create_shipment_confirmation_request_partner(shipment_id, data, current_user, db)


class BulkShipmentStatusRequest(BaseModel):
    shipment_ids: List[int]
    status: str
    notes: str | None = None


@router.put("/shipments/bulk-status")
def bulk_update_shipments_status(
    body: BulkShipmentStatusRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Bulk-update shipment status for multiple shipments (up to 100).
    Partners can only update their own assigned shipments.
    Note: 'delivered' requires signature — use the single-shipment endpoint instead.
    """
    return ctrl.bulk_update_shipment_status_partner(
        body.shipment_ids, body.status, body.notes, current_user, db
    )


# ── Logistics Partner Bank Account (Payout Beneficiary) ───────────────────────

@router.get("/me/bank-account")
def get_partner_bank_account(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get the logistics partner's saved payout bank account."""
    return ctrl.get_partner_bank_account(current_user, db)


@router.put("/me/bank-account")
def upsert_partner_bank_account(
    body: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Submit or update the logistics partner's payout bank account. Triggers admin verification."""
    return ctrl.upsert_partner_bank_account(body, current_user, db)


@router.get("/me/cod-remittance-receipts")
def list_my_cod_remittance_receipts(
    status: Optional[str] = Query(None),
    settlement_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.list_partner_cod_remittance_receipts(current_user, db, status=status, settlement_id=settlement_id)


@router.post("/me/cod-remittance-receipts", status_code=201)
async def upload_my_cod_remittance_receipt(
    settlement_id: int = Form(...),
    amount: float = Form(...),
    bank_reference: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await ctrl.upload_partner_cod_remittance_receipt(
        settlement_id,
        amount,
        file,
        bank_reference,
        notes,
        current_user,
        db,
    )


# ── Logistics Partner Documents ───────────────────────────────────────────────

@router.get("/me/docs")
def list_lp_documents(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List all KYC/compliance documents submitted by the authenticated logistics partner."""
    return ctrl.list_partner_documents(current_user, db)


@router.post("/me/docs/upload")
async def upload_lp_document(
    file: UploadFile = File(...),
    document_type: str = Form(...),
    document_name: str = Form(""),
    expires_at: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Upload a KYC/compliance document (multipart/form-data)."""
    return await ctrl.upload_partner_document(file, document_type, document_name, expires_at, current_user, db)


@router.delete("/me/docs/{doc_id}")
def delete_lp_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Delete a pending or rejected document."""
    return ctrl.delete_partner_document(doc_id, current_user, db)


@router.post("/admin/docs/{doc_id}/review")
def admin_review_lp_document(
    doc_id: int,
    body: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Admin reviews a logistics partner document — approve/reject."""
    return ctrl.admin_review_lp_document(doc_id, body, current_user, db)


# ── City Distance Matrix (admin only) ─────────────────────────────────────────

@router.get("/city-distances")
def list_city_distances(
    origin_country_code: Optional[str] = Query(None),
    destination_country_code: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Admin: list city distance matrix entries with optional filtering."""
    return ctrl.list_city_distances(current_user, db, origin_country_code=origin_country_code, destination_country_code=destination_country_code, q=q, page=page, page_size=page_size)


@router.post("/city-distances")
def create_city_distance(
    body: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Admin: create a new city distance matrix entry."""
    return ctrl.create_city_distance(body, current_user, db)


@router.put("/city-distances/{matrix_id}")
def update_city_distance(
    matrix_id: int,
    body: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Admin: update distance_km (and optional notes) for an existing entry."""
    return ctrl.update_city_distance(matrix_id, body, current_user, db)


@router.delete("/city-distances/{matrix_id}")
def delete_city_distance(
    matrix_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Admin: delete a city distance matrix entry."""
    return ctrl.delete_city_distance(matrix_id, current_user, db)


# === From shipments.py ===
"""Shipments router."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from infrastructure.database.database import get_db
from infrastructure.database.schemas import (
    ShipmentCreate,
    ShipmentEventCreate,
    ShipmentEventOut,
    ShipmentOut,
    ShipmentUpdate,
)
from domains.governance.models.user import User
from domains.logistics.models.logistics_entities import Shipment
from domains.logistics.models.logistics_entities import ShipmentEvent
from infrastructure.utils.dependencies import get_current_user, require_admin, require_logistics

__router_prefix__ = "/shipments"

@router.get("/{shipment_id}", response_model=ShipmentOut)
def get_shipment(shipment_id: int, db: Session = Depends(get_db)):
    s = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not s: raise HTTPException(404, "Not found")
    return s

@router.get("/track/{tracking_number}", response_model=ShipmentOut)
def track_shipment(tracking_number: str, db: Session = Depends(get_db)):
    s = db.query(Shipment).filter(Shipment.tracking_number == tracking_number).first()
    if not s: raise HTTPException(404, "Tracking number not found")
    return s

@router.post("", response_model=ShipmentOut, status_code=201)
def create_shipment(payload: ShipmentCreate, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    s = Shipment(**payload.model_dump())
    db.add(s); db.commit(); db.refresh(s)
    return s

@router.put("/{shipment_id}", response_model=ShipmentOut)
def update_shipment(shipment_id: int, payload: ShipmentUpdate, _: User = Depends(require_logistics), db: Session = Depends(get_db)):
    s = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not s: raise HTTPException(404, "Not found")
    for k, v in payload.model_dump(exclude_unset=True).items(): setattr(s, k, v)
    db.commit(); db.refresh(s)
    return s

@router.post("/{shipment_id}/events", response_model=ShipmentEventOut, status_code=201)
def add_event(shipment_id: int, payload: ShipmentEventCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    s = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not s: raise HTTPException(404, "Not found")
    event = ShipmentEvent(shipment_id=shipment_id, created_by=current_user.id, **payload.model_dump())
    db.add(event); db.commit(); db.refresh(event)
    return event


# === From parcel_tracking.py ===
"""parcel tracking router.

Functional router placeholder. Implement domain endpoints here,
delegating to the appropriate controller/service.
"""
from fastapi import APIRouter


@router.get("/parcel_tracking/health")
def health():
    """Liveness probe for this router."""
    return {"status": "ok", "router": "parcel_tracking", "prefix": "/api/v1/parcel-tracking"}


# === From shipments.py.fixed_tmp ===
"""Shipments router (AXIS 1 — MODULE = who).

Thin HTTP surface only: auth context + require_feature gate + ONE call into the
logistics domain service. All DB writes live in
``domains.logistics.services.shipment_service`` (Law 2).
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from infrastructure.database.database import get_db
from infrastructure.database.schemas import (
    ShipmentCreate,
    ShipmentEventCreate,
    ShipmentEventOut,
    ShipmentOut,
    ShipmentUpdate,
)
from infrastructure.utils.dependencies import require_admin, require_logistics
from modules.logistics.auth import get_current_user
from rbac.dependencies import require_feature

from domains.logistics.services.shipment_service import (
    add_shipment_event,
    create_shipment,
    get_shipment,
    track_shipment,
    update_shipment,
)

__router_prefix__ = "/shipments"


@router.get("/{shipment_id}", response_model=ShipmentOut)
def get_shipment_route(
    shipment_id: int,
    _: None = Depends(require_feature("logistics.shipments.read")),
    db: Session = Depends(get_db),
):
    return get_shipment(db, shipment_id)


@router.get("/track/{tracking_number}", response_model=ShipmentOut)
def track_shipment_route(
    tracking_number: str,
    _: None = Depends(require_feature("logistics.shipments.read")),
    db: Session = Depends(get_db),
):
    return track_shipment(db, tracking_number)


@router.post("/create_shipment", response_model=ShipmentOut, status_code=201)
def create_shipment_route(
    payload: ShipmentCreate,
    _: None = Depends(require_admin),
    _f: None = Depends(require_feature("logistics.shipments.post")),
    db: Session = Depends(get_db),
):
    return create_shipment(db, payload.model_dump())


@router.put("/{shipment_id}", response_model=ShipmentOut)
def update_shipment_route(
    shipment_id: int,
    payload: ShipmentUpdate,
    _: None = Depends(require_logistics),
    _f: None = Depends(require_feature("logistics.shipments.put")),
    db: Session = Depends(get_db),
):
    return update_shipment(db, shipment_id, payload.model_dump(exclude_unset=True))


@router.post("/{shipment_id}/events", response_model=ShipmentEventOut, status_code=201)
def add_event(
    shipment_id: int,
    payload: ShipmentEventCreate,
    current_user=Depends(get_current_user),
    _f: None = Depends(require_feature("logistics.shipments.post")),
    db: Session = Depends(get_db),
):
    return add_shipment_event(db, shipment_id, current_user.id, payload.model_dump())

