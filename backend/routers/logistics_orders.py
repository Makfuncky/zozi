"""Logistics partner orders router."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from data.db import get_db
from data.models import Shipment, LogisticsPartner, User
from utils.dependencies import require_logistics

router = APIRouter()

@router.get("")
def list_assigned_shipments(
    current_user: User = Depends(require_logistics),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    partner = db.query(LogisticsPartner).filter(LogisticsPartner.user_id == current_user.id).first()
    if not partner: raise HTTPException(404)
    shipments = db.query(Shipment).filter(Shipment.assigned_partner_id == partner.id).offset(skip).limit(limit).all()
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

