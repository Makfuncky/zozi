"""
Country Map Router
GeoJSON endpoints for country map system.
"""
import json
import logging
from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from db.database import get_db
from models import CountryConfig, CountryCity, CountryMapConfig

router = APIRouter(tags=["maps"])

logger = logging.getLogger(__name__)


@router.get("/{country_code}/map.geojson")
def get_country_map(
    country_code: str = Path(..., description="Country code"),
    include_cities: bool = Query(True, description="Include cities in map"),
    db: Session = Depends(get_db)
):
    """Get GeoJSON map data for a country."""
    config = db.query(CountryConfig).filter(
        CountryConfig.code == country_code.upper()
    ).first()
    
    if not config:
        raise HTTPException(status_code=404, detail="Country not found")
    
    map_config = db.query(CountryMapConfig).filter(
        CountryMapConfig.country_code == country_code.upper()
    ).first()
    
    geojson = {
        "type": "FeatureCollection",
        "features": []
    }
    
    if config.regions_json:
        try:
            regions = json.loads(config.regions_json) if isinstance(config.regions_json, str) else config.regions_json
            for region in regions:
                feature = {
                    "type": "Feature",
                    "geometry": region.get("geometry"),
                    "properties": {
                        "name": region.get("name"),
                        "type": "region",
                        "code": region.get("code")
                    }
                }
                if feature["geometry"]:
                    geojson["features"].append(feature)
        except (json.JSONDecodeError, TypeError):
            pass
    
    if include_cities:
        cities = db.query(CountryCity).filter(
            CountryCity.country_code == country_code.upper(),
            CountryCity.is_active == True
        ).all()
        
        for city in cities:
            if city.latitude and city.longitude:
                feature = {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [float(city.longitude), float(city.latitude)]
                    },
                    "properties": {
                        "name": city.name,
                        "type": "city",
                        "region": city.region,
                        "population": city.population
                    }
                }
                geojson["features"].append(feature)
    
    return geojson


@router.get("/maps/{country_code}")
def get_country_map_config(
    country_code: str = Path(..., description="Country code"),
    db: Session = Depends(get_db)
):
    """Get map configuration for a country."""
    config = db.query(CountryMapConfig).filter(
        CountryMapConfig.country_code == country_code.upper()
    ).first()
    
    if not config:
        return {
            "country_code": country_code,
            "map_provider": "google",
            "default_zoom": 5,
            "show_regions": True,
            "show_cities": True
        }
    
    return {
        "country_code": country_code,
        "map_provider": config.map_provider,
        "api_key_ref": config.api_key_ref,
        "default_zoom": config.default_zoom,
        "show_regions": config.show_regions,
        "show_cities": config.show_cities
    }
