"""
Logistics Partner Location Router
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query

from data.dependencies_auth import get_current_user
from data.services_logistics_locations_service import (
    list_logistics_partner_locations,
    create_logistics_partner_location,
)

router = APIRouter(tags=["logistics-locations"])
logger = logging.getLogger(__name__)


@router.get("/{country_code}/locations/logistics-partners", response_model=List[dict])
def list_logistics_partner_locations_endpoint(
    country_code: str = Path(...),
    partner_id: Optional[int] = Query(None),
    is_active: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user=Depends(get_current_user),
):
    return list_logistics_partner_locations(country_code, partner_id, is_active, skip, limit)


@router.post("/{country_code}/locations/logistics-partners", response_model=dict)
def create_logistics_partner_location_endpoint(
    country_code: str = Path(...),
    payload: dict = None,
    current_user=Depends(get_current_user),
):
    return create_logistics_partner_location(country_code, payload)
