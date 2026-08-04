"""
Logistics Partner Order Management Router — full lifecycle.
"""
from __future__ import annotations
from typing import List

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from data.db import get_db
from data.models import User
from utils.dependencies import require_logistics, require_admin
from services.orders.order_tracking_service import (
    get_available_orders_for_logistics,
    get_order_shipment_label,
    logistics_confirm_pickup,
    logistics_scan_and_receive,
    logistics_update_transit_status,
    logistics_deliver_order,
    logistics_cancel_pickup,
)
from services.orders.orders_router_service import (
    get_logistics_partner_by_user,
    get_shipments_for_partner,
)

router = APIRouter()


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


@router.get("/available")
def list_available_orders(
    current_user: User = Depends(require_logistics),
    db: Session = Depends(get_db),
):
    """List all orders in 'prepared' status available for pickup."""
    return get_available_orders_for_logistics(db)


@router.get("/my")
def list_my_pickups(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_logistics),
    db: Session = Depends(get_db),
):
    """List shipments assigned to this logistics partner."""
    partner = get_logistics_partner_by_user(db, current_user.id)
    if not partner:
        raise HTTPException(404, "Logistics partner profile not found")
    return get_shipments_for_partner(db, partner.id, skip, limit)


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
    """Update transit sub-status."""
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
    label = get_order_shipment_label(db, order_id)
    if not label:
        raise HTTPException(404, "Order not found")
    return label