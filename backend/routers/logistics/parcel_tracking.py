"""
Parcel Location Tracking Router
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from db.database import get_db
from models import ParcelLocationTracker, CountryConfig, Shipment
from dependencies.auth import get_current_user

from services.write_helpers import add_and_flush, commit_and_refresh
router = APIRouter(tags=["parcel-tracking"])
logger = logging.getLogger(__name__)


@router.get("/parcel/{parcel_id}/tracking", response_model=List[dict])
def list_parcel_tracking(
    parcel_id: int = Path(...),
    country_code: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    query = db.query(ParcelLocationTracker).filter(
        ParcelLocationTracker.parcel_id == parcel_id
    )
    if country_code:
        query = query.filter(ParcelLocationTracker.country_code == country_code.upper())
    locations = query.order_by(ParcelLocationTracker.timestamp.desc()).limit(limit).all()
    return [
        {
            "id": loc.id,
            "parcel_id": loc.parcel_id,
            "country_code": loc.country_code,
            "latitude": loc.latitude,
            "longitude": loc.longitude,
            "location_name": loc.location_name,
            "timestamp": loc.timestamp,
            "created_at": loc.created_at,
        }
        for loc in locations
    ]


@router.post("/parcel/{parcel_id}/tracking", response_model=dict)
def create_parcel_tracking(
    parcel_id: int = Path(...),
    payload: dict = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if not payload:
        payload = {}
    
    shipment = db.query(Shipment).filter(Shipment.id == parcel_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Parcel not found")
    
    location = ParcelLocationTracker(
        parcel_id=parcel_id,
        country_code=payload.get("country_code"),
        latitude=payload.get("latitude"),
        longitude=payload.get("longitude"),
        location_name=payload.get("location_name"),
    )
    add_and_flush(db, location)
    commit_and_refresh(db, location)
    return {"id": location.id, "message": "Parcel tracking entry created"}
