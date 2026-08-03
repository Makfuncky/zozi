"""
Parcel Location Tracking Router
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query

from data.dependencies_auth import get_current_user
from data.services_logistics_parcel_tracking_service import (
    list_parcel_tracking,
    create_parcel_tracking,
)

router = APIRouter(tags=["parcel-tracking"])
logger = logging.getLogger(__name__)


@router.get("/parcel/{parcel_id}/tracking", response_model=List[dict])
def list_parcel_tracking_endpoint(
    parcel_id: int = Path(...),
    country_code: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    current_user=Depends(get_current_user),
):
    return list_parcel_tracking(parcel_id, country_code, limit)


@router.post("/parcel/{parcel_id}/tracking", response_model=dict)
def create_parcel_tracking_endpoint(
    parcel_id: int = Path(...),
    payload: dict = None,
    current_user=Depends(get_current_user),
):
    return create_parcel_tracking(parcel_id, payload)
