"""Logistics logistics router — consolidated from 12 source files."""

import logging
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Path, Query, Request, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from infrastructure.security.dependencies import get_current_user, require_admin, require_logistics
from infrastructure.database.database import get_db
from infrastructure.utils.pagination import paginated_response
from rbac import get_current_user as rbac_get_current_user
from rbac.dependencies import require_feature

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/api/v1/logistics/logistics", tags=["logistics"])


# === Health (from logistics_health.py) ===

@router.get("/health/logistics/{partner_id}")
def get_logistics_health(
    partner_id: int,
    country_code: str = None,
    current_user: dict = Depends(rbac_get_current_user),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("logistics.shipping.tracking")),
):
    from domains.logistics.services.health.service import get_logistics_health_engine
    engine = get_logistics_health_engine(db)
    return engine.calculate_health_score(partner_id, country_code)


@router.get("/health/logistics")
def list_logistics_health(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Items per page (max 100)"),
    country_code: str = None,
    current_user: dict = Depends(rbac_get_current_user),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("logistics.shipping.tracking")),
):
    from domains.logistics.services.health.service import list_logistics_health_paginated
    return list_logistics_health_paginated(db, country_code=country_code, page=page, limit=limit)


# === Logistics Partner Locations (from logistics_locations.py) ===

@router.get("/{country_code}/locations/logistics-partners", response_model=List[dict])
def list_logistics_partner_locations(
    country_code: str = Path(...),
    partner_id: Optional[int] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(rbac_get_current_user),
    _rf_gate: None = Depends(require_feature("logistics.shipping.tracking")),
):
    from domains.logistics.services.geo.logistics_locations_service import list_logistics_partner_locations as _svc_list
    return _svc_list(country_code, partner_id, is_active, db, current_user)


@router.post("/{country_code}/locations/logistics-partners", response_model=dict)
def create_logistics_partner_location(
    country_code: str = Path(...),
    payload: dict = None,
    db: Session = Depends(get_db),
    current_user=Depends(rbac_get_current_user),
    _rf_gate: None = Depends(require_feature("logistics.shipping.manage")),
):
    from domains.logistics.services.geo.logistics_locations_service import create_logistics_partner_location as _svc_create
    return _svc_create(country_code, payload, db, current_user)


# === Logistics Status (from logistics_logistics_status.py) ===

import domains.orders.services.logistics_controller as ctrl


# ── Summary ────────────────────────────────────────────────────────────────────

@router.get("/summary")
async def get_logistics_summary(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("logistics.shipping.tracking")),
):
    return await ctrl.get_logistics_summary(current_user, db)


# ── Carriers ──────────────────────────────────────────────────────────────────

@router.get("/carriers")
async def get_carriers(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("logistics.shipping.tracking")),
):
    return await ctrl.get_carriers(current_user, db)


@router.post("/carriers")
async def create_carrier(
    data: dict[str, Any],
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("logistics.shipping.manage")),
):
    return await ctrl.create_carrier(data, current_user, db)


@router.delete("/carriers/{carrier_id}")
async def delete_carrier(
    carrier_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("logistics.shipping.manage")),
):
    return await ctrl.delete_carrier(carrier_id, current_user, db)


# ── Shipping Zones ────────────────────────────────────────────────────────────

@router.get("/zones")
async def get_shipping_zones(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("logistics.shipping.tracking")),
):
    return await ctrl.get_shipping_zones(current_user, db)


@router.post("/zones")
async def upsert_shipping_zone(
    data: dict[str, Any],
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("logistics.shipping.manage")),
):
    return await ctrl.upsert_shipping_zone(data, current_user, db)


@router.put("/zones/{zone_id}")
async def update_shipping_zone(
    zone_id: int,
    data: dict[str, Any],
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("logistics.shipping.manage")),
):
    data["id"] = zone_id
    return await ctrl.upsert_shipping_zone(data, current_user, db)


@router.delete("/zones/{zone_id}")
async def delete_shipping_zone(
    zone_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("logistics.shipping.manage")),
):
    return await ctrl.delete_shipping_zone(zone_id, current_user, db)


# ── Orders to Fulfil ──────────────────────────────────────────────────────────

@router.get("/orders/pending")
async def get_orders_to_fulfil(
    limit: int = 200,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("logistics.fulfillment.manage")),
):
    return await ctrl.get_orders_to_fulfil(current_user, db, limit=limit, offset=offset)


# ── Shipments ─────────────────────────────────────────────────────────────────

@router.post("/shipments")
async def create_shipment(
    data: dict[str, Any],
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("logistics.shipping.manage")),
):
    return await ctrl.create_shipment(data, current_user, db)


@router.get("/shipments/scan")
async def scan_lookup_shipment(
    code: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("logistics.shipping.tracking")),
):
    """Look up a shipment by tracking number or scan code. Admin only."""
    from domains.logistics.services.shipping.shipments_service import scan_lookup_shipment_by_code
    return scan_lookup_shipment_by_code(code, db, current_user)


@router.put("/shipments/{shipment_id}/status")
async def admin_update_shipment_status(
    shipment_id: int,
    data: dict[str, Any],
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("logistics.shipping.manage")),
):
    """Admin endpoint to update a shipment status directly (bypasses supplier check)."""
    from domains.logistics.services.shipping.shipments_service import admin_update_shipment_status_service
    return admin_update_shipment_status_service(shipment_id, data, db, current_user)


@router.get("/shipments/active")
async def get_active_shipments(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("logistics.shipping.tracking")),
):
    return await ctrl.get_active_shipments(current_user, db)


@router.get("/shipments/history")
async def get_shipment_history(
    page: int = 1,
    per_page: int = 30,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("logistics.shipping.tracking")),
):
    return await ctrl.get_shipment_history(current_user, db, page=page, per_page=per_page)


@router.get("/shipments/{shipment_id}/events")
async def get_shipment_events(
    shipment_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("logistics.shipping.tracking")),
):
    return await ctrl.get_shipment_events(shipment_id, current_user, db)


@router.post("/shipments/{shipment_id}/scan")
async def scan_shipment_event(
    shipment_id: int,
    data: dict[str, Any],
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("logistics.shipping.manage")),
):
    return await ctrl.scan_shipment_event(shipment_id, data, current_user, db)


@router.patch("/shipments/{shipment_id}")
async def update_shipment_status(
    shipment_id: int,
    data: dict[str, Any],
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("logistics.shipping.manage")),
):
    return await ctrl.update_shipment_status(shipment_id, data, current_user, db)


@router.get("/distribution/channels")
async def get_distribution_channels(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("logistics.shipping.tracking")),
):
    return await ctrl.get_distribution_channels(current_user, db)


# ── GPS Event Update ─────────────────────────────────────────────────────────

@router.patch("/events/{event_id}/gps")
async def update_shipment_event_gps(
    event_id: int,
    data: dict[str, Any],
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("logistics.shipping.manage")),
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


# === Logistics Orders (from logistics_orders_list.py) ===

from domains.accounts.models.user import User


@router.get("")
def list_assigned_shipments(current_user: User = Depends(require_logistics), db: Session = Depends(get_db)):
    from domains.logistics.services.geo.logistics_locations_service import list_assigned_shipments as _svc_list
    return _svc_list(db, current_user)


# === Logistics Orders V2 (from logistics_orders_v2.py) ===

from domains.orders.ports import (
    get_available_orders_for_logistics,
    get_order_shipment_label,
    logistics_cancel_pickup,
    logistics_confirm_pickup,
    logistics_deliver_order,
    logistics_scan_and_receive,
    logistics_update_transit_status,
)


# ── Pydantic schemas for POST bodies ───────────────────────────────

class ScanReceiveRequest(BaseModel):
    scan_code: str
    location: Optional[str] = None

class UpdateTransitRequest(BaseModel):
    event_type: str
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
    _rf_gate: None = Depends(require_feature("logistics.fulfillment.manage")),
):
    """List all orders in 'prepared' status available for pickup."""
    return get_available_orders_for_logistics(db)


@router.get("/my")
def list_my_pickups(
    current_user: User = Depends(require_logistics),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("logistics.fulfillment.manage")),
):
    """List shipments assigned to this logistics partner."""
    from domains.logistics.services.geo.logistics_locations_service import list_my_pickups as _svc_pickups
    return _svc_pickups(db, current_user)


@router.post("/{order_id}/confirm-pickup")
def confirm_pickup(
    order_id: int,
    current_user: User = Depends(require_logistics),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("logistics.fulfillment.manage")),
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
    _rf_gate: None = Depends(require_feature("logistics.shipping.manage")),
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
    _rf_gate: None = Depends(require_feature("logistics.fulfillment.manage")),
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
    _rf_gate: None = Depends(require_feature("logistics.fulfillment.manage")),
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
    _rf_gate: None = Depends(require_feature("logistics.fulfillment.manage")),
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
    _rf_gate: None = Depends(require_feature("logistics.shipping.tracking")),
):
    """Get packing label data for printing (includes QR code, customer info, lat/lng)."""
    label = get_order_shipment_label(order_id, db)
    if not label:
        raise HTTPException(404, "Order not found")
    return label


# === Logistics Partner (from logistics_partner.py) ===

import domains.orders.services.logistics_partner_controller as partner_ctrl


@router.get("/public")
def list_public_logistics_partners(
    request: Request,
    q: Optional[str] = Query(None),
    country: Optional[str] = Query(None, min_length=2, max_length=10),
    limit: int = Query(12, ge=1, le=50),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("logistics.shipping.tracking")),
):
    resolved_country = (
        country
        or request.headers.get("X-Country-Code")
        or getattr(request.state, "country_code", None)
    )
    return partner_ctrl.list_public_partners(db, q=q, country=resolved_country, limit=limit)


@router.get("/public/{partner_id}")
def get_public_logistics_partner(
    partner_id: int,
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("logistics.shipping.tracking")),
):
    return partner_ctrl.get_public_partner(partner_id, db)


@router.get("/profile")
def get_partner_profile(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("logistics.partners.manage")),
):
    return partner_ctrl.get_my_partner_profile(current_user, db)


@router.put("/profile")
def update_partner_profile(
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("logistics.partners.manage")),
):
    return partner_ctrl.update_my_partner_profile(data, current_user, db)


@router.post("/profile/terms/accept")
def accept_partner_profile_terms(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("logistics.partners.manage")),
):
    return partner_ctrl.accept_partner_terms(current_user, db)


@router.post("/profile/submit-review")
def submit_partner_profile_review(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("logistics.partners.manage")),
):
    return partner_ctrl.submit_partner_profile_for_review(current_user, db)


@router.get("/service-areas")
def get_partner_service_areas(
    partner_id: Optional[int] = Query(None),
    approval_status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("logistics.partners.manage")),
):
    return partner_ctrl.list_my_partner_service_areas(
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
    _rf_gate: None = Depends(require_feature("logistics.sla.manage")),
):
    return partner_ctrl.list_my_partner_pricing_profiles(
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
    _rf_gate: None = Depends(require_feature("logistics.sla.manage")),
):
    return partner_ctrl.list_my_partner_category_rules(
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
    _rf_gate: None = Depends(require_feature("logistics.sla.manage")),
):
    return partner_ctrl.list_my_partner_vehicle_rules(
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
    _rf_gate: None = Depends(require_feature("logistics.sla.manage")),
):
    return partner_ctrl.get_partner_pricing_insights(
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
    _rf_gate: None = Depends(require_feature("logistics.sla.manage")),
):
    return partner_ctrl.upsert_my_partner_pricing_profile(None, data, current_user, db)


@router.put("/pricing-profiles/{profile_id}")
def update_partner_pricing_profile(
    profile_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("logistics.sla.manage")),
):
    return partner_ctrl.upsert_my_partner_pricing_profile(profile_id, data, current_user, db)


@router.delete("/pricing-profiles/{profile_id}")
def delete_partner_pricing_profile(
    profile_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("logistics.sla.manage")),
):
    return partner_ctrl.delete_my_partner_pricing_profile(profile_id, current_user, db)


@router.post("/category-rules")
def create_partner_category_rule(
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("logistics.sla.manage")),
):
    return partner_ctrl.upsert_my_partner_category_rule(None, data, current_user, db)


@router.put("/category-rules/{rule_id}")
def update_partner_category_rule(
    rule_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("logistics.sla.manage")),
):
    return partner_ctrl.upsert_my_partner_category_rule(rule_id, data, current_user, db)


@router.delete("/category-rules/{rule_id}")
def delete_partner_category_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("logistics.sla.manage")),
):
    return partner_ctrl.delete_my_partner_category_rule(rule_id, current_user, db)


@router.post("/vehicle-rules")
def create_partner_vehicle_rule(
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("logistics.sla.manage")),
):
    return partner_ctrl.upsert_my_partner_vehicle_rule(None, data, current_user, db)


@router.put("/vehicle-rules/{rule_id}")
def update_partner_vehicle_rule(
    rule_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("logistics.sla.manage")),
):
    return partner_ctrl.upsert_my_partner_vehicle_rule(rule_id, data, current_user, db)


@router.delete("/vehicle-rules/{rule_id}")
def delete_partner_vehicle_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("logistics.sla.manage")),
):
    return partner_ctrl.delete_my_partner_vehicle_rule(rule_id, current_user, db)


@router.post("/service-areas")
def create_partner_service_area(
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("logistics.partners.manage")),
):
    return partner_ctrl.upsert_my_partner_service_area(None, data, current_user, db)


@router.put("/service-areas/{area_id}")
def update_partner_service_area(
    area_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("logistics.partners.manage")),
):
    return partner_ctrl.upsert_my_partner_service_area(area_id, data, current_user, db)


@router.delete("/service-areas/{area_id}")
def delete_partner_service_area(
    area_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("logistics.partners.manage")),
):
    return partner_ctrl.delete_my_partner_service_area(area_id, current_user, db)


@router.post("/review/profile/{partner_id}")
def review_logistics_partner_profile(
    partner_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("logistics.partners.manage")),
):
    return partner_ctrl.review_partner_profile(partner_id, data, current_user, db)


@router.post("/review/service-areas/{area_id}")
def review_logistics_partner_service_area(
    area_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("logistics.partners.manage")),
):
    return partner_ctrl.review_partner_service_area(area_id, data, current_user, db)


@router.post("/review/pricing-profiles/{profile_id}")
def review_logistics_partner_pricing_profile(
    profile_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("logistics.sla.manage")),
):
    return partner_ctrl.review_partner_pricing_profile(profile_id, data, current_user, db)


@router.post("/review/category-rules/{rule_id}")
def review_logistics_partner_category_rule(
    rule_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("logistics.sla.manage")),
):
    return partner_ctrl.review_partner_category_rule(rule_id, data, current_user, db)


@router.post("/review/vehicle-rules/{rule_id}")
def review_logistics_partner_vehicle_rule(
    rule_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("logistics.sla.manage")),
):
    return partner_ctrl.review_partner_vehicle_rule(rule_id, data, current_user, db)


@router.post("/shipping-quote")
def get_logistics_shipping_quote(
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("logistics.shipping.tracking")),
):
    return partner_ctrl.shipping_quote_for_customer(data, db)


# ── Admin: manage partners ────────────────────────────────────────────────────

@router.get("/")
def list_partners(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("logistics.partners.manage")),
):
    """Admin: list all logistics partners."""
    return partner_ctrl.list_partners(current_user, db)


@router.post("/", status_code=201)
def create_partner(
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("logistics.partners.manage")),
):
    """Admin: onboard a new logistics partner."""
    return partner_ctrl.create_partner(data, current_user, db)


class BulkPartnerAdminActionRequest(BaseModel):
    partner_ids: List[int]
    action: str
    note: str | None = None


@router.post("/bulk")
def bulk_manage_logistics_partners(
    body: BulkPartnerAdminActionRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("logistics.shipping.manage")),
):
    """Admin bulk actions for logistics partner review and portal lifecycle."""
    return partner_ctrl.bulk_manage_partners(body.partner_ids, body.action, body.note, current_user, db)


@router.put("/{partner_id}")
def update_partner(
    partner_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("logistics.shipping.manage")),
):
    """Admin: update partner details or status."""
    return partner_ctrl.update_partner(partner_id, data, current_user, db)


@router.delete("/{partner_id}")
def delete_partner(
    partner_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("logistics.shipping.manage")),
):
    """Admin-only: remove a logistics partner."""
    return partner_ctrl.delete_partner(partner_id, current_user, db)


# ── Partner Dashboard ─────────────────────────────────────────────────────────

@router.get("/dashboard")
def partner_dashboard(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("logistics.shipping.tracking")),
):
    """Dashboard stats for logistics partner or admin."""
    return partner_ctrl.get_partner_dashboard(current_user, db)


@router.get("/analytics")
def partner_analytics(
    period: str = Query("30d", description="Analytics lookback window: 7d, 30d, or 90d"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("logistics.shipping.tracking")),
):
    return partner_ctrl.get_partner_analytics(current_user, db, period=period)


@router.get("/payouts")
def partner_payouts(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("logistics.partners.manage")),
):
    return partner_ctrl.get_partner_payouts(current_user, db)


@router.post("/payouts/request")
def request_payout(
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("logistics.partners.manage")),
):
    return partner_ctrl.request_partner_payout(data, current_user, db)


@router.get("/payouts/pending")
def pending_payouts(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("logistics.partners.manage")),
):
    return partner_ctrl.list_pending_partner_payouts(current_user, db)


@router.post("/payouts/{payout_id}/verify")
def verify_payout(
    payout_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("logistics.partners.manage")),
):
    return partner_ctrl.verify_partner_payout(payout_id, data, current_user, db)


@router.get("/shipments")
def list_partner_shipments(
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("logistics.shipping.tracking")),
):
    """List shipments assigned to (or visible by) this logistics partner."""
    return partner_ctrl.get_partner_shipments(current_user, db, status=status, page=page, page_size=page_size)


@router.post("/shipments/{shipment_id}/confirmation-request")
def create_shipment_confirmation_request(
    shipment_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("logistics.shipping.manage")),
):
    """Partner creates a pending pickup or delivery confirmation request."""
    return partner_ctrl.create_shipment_confirmation_request_partner(shipment_id, data, current_user, db)


class BulkShipmentStatusRequest(BaseModel):
    shipment_ids: List[int]
    status: str
    notes: str | None = None


@router.put("/shipments/bulk-status")
def bulk_update_shipments_status(
    body: BulkShipmentStatusRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("logistics.shipping.manage")),
):
    """Bulk-update shipment status for multiple shipments (up to 100).
    Partners can only update their own assigned shipments.
    Note: 'delivered' requires signature — use the single-shipment endpoint instead.
    """
    return partner_ctrl.bulk_update_shipment_status_partner(
        body.shipment_ids, body.status, body.notes, current_user, db
    )


# ── Logistics Partner Bank Account (Payout Beneficiary) ───────────────────────

@router.get("/me/bank-account")
def get_partner_bank_account(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("logistics.partners.manage")),
):
    """Get the logistics partner's saved payout bank account."""
    return partner_ctrl.get_partner_bank_account(current_user, db)


@router.put("/me/bank-account")
def upsert_partner_bank_account(
    body: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("logistics.partners.manage")),
):
    """Submit or update the logistics partner's payout bank account. Triggers admin verification."""
    return partner_ctrl.upsert_partner_bank_account(body, current_user, db)


@router.get("/me/cod-remittance-receipts")
def list_my_cod_remittance_receipts(
    status: Optional[str] = Query(None),
    settlement_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("logistics.partners.manage")),
):
    return partner_ctrl.list_partner_cod_remittance_receipts(current_user, db, status=status, settlement_id=settlement_id)


@router.post("/me/cod-remittance-receipts", status_code=201)
async def upload_my_cod_remittance_receipt(
    settlement_id: int = Form(...),
    amount: float = Form(...),
    bank_reference: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("logistics.partners.manage")),
):
    return await partner_ctrl.upload_partner_cod_remittance_receipt(
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
    _rf_gate: None = Depends(require_feature("logistics.partners.manage")),
):
    """List all KYC/compliance documents submitted by the authenticated logistics partner."""
    return partner_ctrl.list_partner_documents(current_user, db)


@router.post("/me/docs/upload")
async def upload_lp_document(
    file: UploadFile = File(...),
    document_type: str = Form(...),
    document_name: str = Form(""),
    expires_at: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("logistics.partners.manage")),
):
    """Upload a KYC/compliance document (multipart/form-data)."""
    return await partner_ctrl.upload_partner_document(file, document_type, document_name, expires_at, current_user, db)


@router.delete("/me/docs/{doc_id}")
def delete_lp_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("logistics.partners.manage")),
):
    """Delete a pending or rejected document."""
    return partner_ctrl.delete_partner_document(doc_id, current_user, db)


@router.post("/admin/docs/{doc_id}/review")
def admin_review_lp_document(
    doc_id: int,
    body: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("logistics.partners.manage")),
):
    """Admin reviews a logistics partner document — approve/reject."""
    return partner_ctrl.admin_review_lp_document(doc_id, body, current_user, db)


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
    _rf_gate: None = Depends(require_feature("logistics.shipping.tracking")),
):
    """Admin: list city distance matrix entries with optional filtering."""
    return partner_ctrl.list_city_distances(current_user, db, origin_country_code=origin_country_code, destination_country_code=destination_country_code, q=q, page=page, page_size=page_size)


@router.post("/city-distances")
def create_city_distance(
    body: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("logistics.shipping.manage")),
):
    """Admin: create a new city distance matrix entry."""
    return partner_ctrl.create_city_distance(body, current_user, db)


@router.put("/city-distances/{matrix_id}")
def update_city_distance(
    matrix_id: int,
    body: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("logistics.shipping.manage")),
):
    """Admin: update distance_km (and optional notes) for an existing entry."""
    return partner_ctrl.update_city_distance(matrix_id, body, current_user, db)


@router.delete("/city-distances/{matrix_id}")
def delete_city_distance(
    matrix_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("logistics.shipping.manage")),
):
    """Admin: delete a city distance matrix entry."""
    return partner_ctrl.delete_city_distance(matrix_id, current_user, db)


# === Parcel Tracking (from parcel_tracking.py) ===

@router.get("/parcel_tracking/health")
def parcel_tracking_health(    _rf_gate: None = Depends(require_feature("logistics.shipping.tracking"))):
    """Liveness probe for this router."""
    return {"status": "ok", "router": "parcel_tracking", "prefix": "/api/v1/parcel-tracking"}
