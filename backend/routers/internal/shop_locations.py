"""
Shop & Warehouse Location Router
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from db.database import get_db
from models import ShopWarehouseLocation, CountryConfig
from dependencies.auth import get_current_user

from services.write_helpers import add_and_flush, commit_and_refresh
router = APIRouter(tags=["shop-locations"])
logger = logging.getLogger(__name__)


@router.get("/{country_code}/locations/shops", response_model=List[dict])
def list_shop_locations(
    country_code: str = Path(...),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    query = db.query(ShopWarehouseLocation).filter(
        ShopWarehouseLocation.country_code == country_code.upper()
    )
    if is_active is not None:
        query = query.filter(ShopWarehouseLocation.is_active == is_active)
    locations = query.order_by(ShopWarehouseLocation.name).all()
    return [
        {
            "id": loc.id,
            "name": loc.name,
            "warehouse_code": loc.warehouse_code,
            "latitude": loc.latitude,
            "longitude": loc.longitude,
            "address": loc.address,
            "is_active": loc.is_active,
            "created_at": loc.created_at,
        }
        for loc in locations
    ]


@router.post("/{country_code}/locations/shops", response_model=dict)
def create_shop_location(
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
    
    location = ShopWarehouseLocation(
        country_code=country_code.upper(),
        name=payload.get("name"),
        warehouse_code=payload.get("warehouse_code"),
        latitude=payload.get("latitude"),
        longitude=payload.get("longitude"),
        address=payload.get("address"),
        is_active=payload.get("is_active", True),
    )
    add_and_flush(db, location)
    commit_and_refresh(db, location)
    return {"id": location.id, "message": "Shop location created"}


@router.put("/{country_code}/locations/shops/{location_id}", response_model=dict)
def update_shop_location(
    country_code: str = Path(...),
    location_id: int = Path(...),
    payload: dict = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if not payload:
        payload = {}
    location = db.query(ShopWarehouseLocation).filter(
        ShopWarehouseLocation.id == location_id,
        ShopWarehouseLocation.country_code == country_code.upper()
    ).first()
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    for field in ["name", "warehouse_code", "latitude", "longitude", "address", "is_active"]:
        if field in payload:
            setattr(location, field, payload[field])
    
    commit_and_refresh(db, location)
    return {"id": location.id, "message": "Shop location updated"}
