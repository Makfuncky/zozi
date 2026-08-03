"""
Logistics Health API Endpoints
"""
from fastapi import APIRouter, Depends, Query

from data.dependencies_auth import get_current_user
from data.services_logistics_health_service import get_logistics_health, list_logistics_health

router = APIRouter()


@router.get("/health/logistics/{partner_id}")
def get_logistics_health_endpoint(
    partner_id: int,
    country_code: str = None,
    current_user: dict = Depends(get_current_user),
):
    return get_logistics_health(partner_id, country_code)


@router.get("/health/logistics")
def list_logistics_health_endpoint(
    country_code: str = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    return list_logistics_health(country_code=country_code, skip=skip, limit=limit)
