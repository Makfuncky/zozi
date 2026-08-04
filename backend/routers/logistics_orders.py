"""Logistics partner orders router."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from data.db import get_db
from data.models import User
from utils.dependencies import require_logistics
from services.logistics.logistics_partner_write_service import (
    get_partner_by_user,
    list_shipments_for_partner,
)

router = APIRouter()

@router.get("")
def list_assigned_shipments(
    current_user: User = Depends(require_logistics),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    partner = get_partner_by_user(db, current_user.id)
    if not partner:
        raise HTTPException(404)
    shipments = list_shipments_for_partner(db, partner.id, skip=skip, limit=limit)
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
