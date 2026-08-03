"""
Country Map Router
GeoJSON endpoints for country map system.
"""
import logging
from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Path, Query

from data.services_country_maps_service import get_country_map, get_country_map_config

router = APIRouter(tags=["maps"])

logger = logging.getLogger(__name__)


@router.get("/{country_code}/map.geojson")
def get_country_map_endpoint(
    country_code: str = Path(..., description="Country code"),
    include_cities: bool = Query(True, description="Include cities in map"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    """Get GeoJSON map data for a country."""
    return get_country_map(country_code, include_cities, skip, limit)


@router.get("/maps/{country_code}")
def get_country_map_config_endpoint(
    country_code: str = Path(..., description="Country code"),
):
    """Get map configuration for a country."""
    return get_country_map_config(country_code)
