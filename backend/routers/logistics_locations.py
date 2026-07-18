"""
Logistics Partner Location Router
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from db.database import get_db
from models import LogisticsPartnerLocation, CountryConfig, LogisticsPartner
from controllers.auth_controller import get_current_user

router = APIRouter(tags=["logistics-locations"])
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
