"""Country map router logic, extracted behind the service layer (clears LC1).

Each function owns its database session via ``data.db.get_db_context`` so the
router layer never injects or touches a SQLAlchemy session directly.
"""
import json
from typing import Optional


def get_country_map(country_code: str, include_cities: bool, skip: int, limit: int) -> dict:
    from data.db import get_db_context
    from data.models import CountryConfig, CountryCity, CountryMapConfig

    cc = country_code.upper()
    with get_db_context() as db:
        config = db.query(CountryConfig).filter(CountryConfig.code == cc).first()
        if not config:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Country not found")

        map_config = db.query(CountryMapConfig).filter(
            CountryMapConfig.country_code == cc
        ).first()

        geojson = {"type": "FeatureCollection", "features": []}

        if config.regions_json:
            try:
                regions = (
                    json.loads(config.regions_json)
                    if isinstance(config.regions_json, str)
                    else config.regions_json
                )
                for region in regions:
                    feature = {
                        "type": "Feature",
                        "geometry": region.get("geometry"),
                        "properties": {
                            "name": region.get("name"),
                            "type": "region",
                            "code": region.get("code"),
                        },
                    }
                    if feature["geometry"]:
                        geojson["features"].append(feature)
            except (json.JSONDecodeError, TypeError):
                pass

        if include_cities:
            cities = (
                db.query(CountryCity)
                .filter(CountryCity.country_code == cc, CountryCity.is_active == True)
                .offset(skip)
                .limit(limit)
                .all()
            )
            for city in cities:
                if city.latitude and city.longitude:
                    feature = {
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [float(city.longitude), float(city.latitude)],
                        },
                        "properties": {
                            "name": city.name,
                            "type": "city",
                            "region": city.region,
                            "population": city.population,
                        },
                    }
                    geojson["features"].append(feature)

        return geojson


def get_country_map_config(country_code: str) -> dict:
    from data.db import get_db_context
    from data.models import CountryMapConfig

    cc = country_code.upper()
    with get_db_context() as db:
        config = db.query(CountryMapConfig).filter(
            CountryMapConfig.country_code == cc
        ).first()
        if not config:
            return {
                "country_code": cc,
                "map_provider": "google",
                "default_zoom": 5,
                "show_regions": True,
                "show_cities": True,
            }
        return {
            "country_code": cc,
            "map_provider": config.map_provider,
            "api_key_ref": config.api_key_ref,
            "default_zoom": config.default_zoom,
            "show_regions": config.show_regions,
            "show_cities": config.show_cities,
        }
