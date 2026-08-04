"""Geo location and country detection endpoints."""
from __future__ import annotations
from typing import List

from typing import Optional

from fastapi import APIRouter, Depends, Query, Request

from data.dependencies_auth import get_current_user
from data.services_location_geo_service import (
    resolve_country_from_ip,
    get_country_details,
    list_geo_countries,
)
from utils.ip_utils import get_request_ip

router = APIRouter()


@router.get("/geo")
def get_geo_info(
    request: Request,
    ip_address: Optional[str] = Query(None, description="Client IP for geo detection"),
    current_user: dict = Depends(get_current_user),
):
    """Get geo information based on IP or user location."""
    country_code = None
    if ip_address:
        country_code = resolve_country_from_ip(ip_address)
    elif hasattr(request.state, "client_ip") and request.state.client_ip != "unknown":
        country_code = resolve_country_from_ip(request.state.client_ip)
    elif current_user.get("preferred_country"):
        country_code = current_user.get("preferred_country")

    return get_country_details(country_code)


@router.get("/geo/countries")
def list_geo_countries_endpoint(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    """List all countries with geo information."""
    return list_geo_countries(skip, limit)
