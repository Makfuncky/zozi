"""
Shop & Warehouse Location Router
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query

from data.dependencies_auth import get_current_user
from data.services_location_shop_locations_service import (
    list_shop_locations,
    create_shop_location,
    update_shop_location,
)

router = APIRouter(tags=["shop-locations"])
logger = logging.getLogger(__name__)


@router.get("/{country_code}/locations/shops", response_model=List[dict])
def list_shop_locations_endpoint(
    country_code: str = Path(...),
    is_active: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user=Depends(get_current_user),
):
    return list_shop_locations(country_code, is_active, skip, limit)


@router.post("/{country_code}/locations/shops", response_model=dict)
def create_shop_location_endpoint(
    country_code: str = Path(...),
    payload: dict = None,
    current_user=Depends(get_current_user),
):
    return create_shop_location(country_code, payload)


@router.put("/{country_code}/locations/shops/{location_id}", response_model=dict)
def update_shop_location_endpoint(
    country_code: str = Path(...),
    location_id: int = Path(...),
    payload: dict = None,
    current_user=Depends(get_current_user),
):
    return update_shop_location(country_code, location_id, payload)
