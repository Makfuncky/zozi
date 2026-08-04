"""Service methods for country maps and staff data access."""
from typing import List
import json
from sqlalchemy.orm import Session
from data.models import CountryCity, CountryStaffAssignment


def get_country_map(country_code: str, include_cities: bool, skip: int, limit: int) -> dict:
    """Return a GeoJSON FeatureCollection for a country (regions + city markers)."""
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
    """Get map display configuration for a country."""
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


def list_country_cities_by_country(db: Session, country_code: str) -> list[CountryCity]:
    """List cities for a country."""
    return db.query(CountryCity).filter(CountryCity.country_code == country_code).all()


def get_country_city_by_id(db: Session, city_id: int) -> CountryCity | None:
    """Get a city by ID."""
    return db.query(CountryCity).filter(CountryCity.id == city_id).first()


def get_country_staff_assignments(
    db: Session, country_code: str, role: str | None = None
) -> list[CountryStaffAssignment]:
    """Get staff assignments for a country."""
    query = db.query(CountryStaffAssignment).filter(
        CountryStaffAssignment.country_code == country_code
    )
    if role:
        query = query.filter(CountryStaffAssignment.role == role)
    return query.order_by(CountryStaffAssignment.start_date.desc()).all()


def get_country_staff_by_id(db: Session, assignment_id: int) -> CountryStaffAssignment | None:
    """Get a staff assignment by ID."""
    return db.query(CountryStaffAssignment).filter(
        CountryStaffAssignment.id == assignment_id
    ).first()


def get_country_staff_by_country(db: Session, country_code: str) -> list[CountryStaffAssignment]:
    """Get all staff for a country."""
    return db.query(CountryStaffAssignment).filter(
        CountryStaffAssignment.country_code == country_code
    ).all()


def list_active_staff_assignments(
    db: Session, country_code: str, skip: int = 0, limit: int = 20
) -> list[CountryStaffAssignment]:
    """List active staff assignments for a country (delegated read for routers)."""
    return (
        db.query(CountryStaffAssignment)
        .filter(
            CountryStaffAssignment.country_code == country_code.upper(),
            CountryStaffAssignment.is_active == True,
        )
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_active_staff_assignment(
    db: Session, country_code: str, user_id: int, role_in_country: str
) -> CountryStaffAssignment | None:
    """Get an existing active staff assignment by country/user/role (delegated read)."""
    return (
        db.query(CountryStaffAssignment)
        .filter(
            CountryStaffAssignment.country_code == country_code.upper(),
            CountryStaffAssignment.user_id == user_id,
            CountryStaffAssignment.role_in_country == role_in_country,
            CountryStaffAssignment.is_active == True,
        )
        .first()
    )


def get_staff_assignment_by_id(
    db: Session, staff_id: int, country_code: str
) -> CountryStaffAssignment | None:
    """Get a staff assignment by id scoped to a country (delegated read)."""
    return (
        db.query(CountryStaffAssignment)
        .filter(
            CountryStaffAssignment.id == staff_id,
            CountryStaffAssignment.country_code == country_code.upper(),
        )
        .first()
    )
