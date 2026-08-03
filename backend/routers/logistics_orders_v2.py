"""
Logistics Partner Order Management Router â€” full lifecycle.
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from data.db import get_db
from data.models import User, LogisticsPartner, Shipment
from utils.dependencies import require_logistics, require_admin
from services.order_tracking_service import (
    get_available_orders_for_logistics,
    get_order_shipment_label,
    logistics_confirm_pickup,
    logistics_scan_and_receive,
    logistics_update_transit_status,
    logistics_deliver_order,
    logistics_cancel_pickup,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# â”€â”€ Pydantic schemas for POST bodies â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

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


# â”€â”€ Endpoints â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

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
    partner = db.query(LogisticsPartner).filter(
        LogisticsPartner.user_id == current_user.id
    ).first()
    if not partner:
        raise HTTPException(404, "Logistics partner profile not found")
    shipments = (
        db.query(Shipment)
        .filter(Shipment.assigned_partner_id == partner.id)
        .order_by(Shipment.updated_at.desc())
        .offset(skip)
        .limit(limit)
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
    """Confirm pickup â€” marks order as 'picking_up' and removes from other logistics lists."""
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
    """Scan QR code and receive package from supplier. Status â†’ shipped/picked_from_supplier."""
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
