"""
Shop & Warehouse Location Router
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from controllers.auth_controller import get_current_user
from db.database import get_db
from data.models import ShopWarehouseLocation
from services.db_read import all_rows
from services.logistics.location_service import create_shop_location, update_shop_location
import structlog
logger = structlog.get_logger(__name__)

router = APIRouter(tags=["shop-locations"])
logger = logging.getLogger(__name__)


@router.get("/{country_code}/locations/shops", response_model=List[dict])
def list_shop_locations(
    country_code: str = Path(...),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    filters = [ShopWarehouseLocation.country_code == country_code.upper()]
    if is_active is not None:
        filters.append(ShopWarehouseLocation.is_active == is_active)
    locations = all_rows(
        db, ShopWarehouseLocation, filters, order_by=ShopWarehouseLocation.name
    )
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
    location = create_shop_location(db, country_code, payload)
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
    location = update_shop_location(db, location_id, country_code, payload)
    return {"id": location.id, "message": "Shop location updated"}
