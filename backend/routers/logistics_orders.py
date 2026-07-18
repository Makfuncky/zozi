"""Logistics partner orders router."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.database import get_db
from models import Shipment, LogisticsPartner, User
from utils.dependencies import require_logistics

router = APIRouter()

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

