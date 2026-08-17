"""
Logistics Partner Order Management Router — full lifecycle.
"""
from __future__ import annotations
import logging
from typing import Optional
from fastapi import Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from db.database import get_db
from _legacy.models import User, LogisticsPartner, Shipment
from utils.dependencies import require_logistics, require_admin
from services.orders.order_tracking_service import get_available_orders_for_logistics, get_order_shipment_label, logistics_confirm_pickup, logistics_scan_and_receive, logistics_update_transit_status, logistics_deliver_order, logistics_cancel_pickup
logger = logging.getLogger(__name__)

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

def list_my_pickups(current_user: User=Depends(require_logistics), db: Session=Depends(get_db)):
    """List shipments assigned to this logistics partner."""
    partner = db.query(LogisticsPartner).filter(LogisticsPartner.user_id == current_user.id).first()
    if not partner:
        raise HTTPException(404, 'Logistics partner profile not found')
    shipments = db.query(Shipment).filter(Shipment.assigned_partner_id == partner.id).order_by(Shipment.updated_at.desc()).all()
    return [{'id': s.id, 'order_id': s.order_id, 'status': s.status, 'tracking_number': s.tracking_number, 'scan_code': s.scan_code, 'current_hub': s.current_hub, 'package_weight_kg': float(s.package_weight_kg) if s.package_weight_kg else None, 'packaged_at': s.packaged_at.isoformat() if s.packaged_at else None, 'shipped_at': s.shipped_at.isoformat() if s.shipped_at else None, 'estimated_delivery': s.estimated_delivery.isoformat() if s.estimated_delivery else None, 'actual_delivery': s.actual_delivery.isoformat() if s.actual_delivery else None, 'delivery_signature_name': s.delivery_signature_name, 'updated_at': s.updated_at.isoformat() if s.updated_at else None} for s in shipments]
