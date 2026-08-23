"""Auto-migrated service logic from routers/country_dropdown.py."""
from __future__ import annotations

from __future__ import annotations

from typing import List, Optional

from fastapi import Depends, HTTPException, Query

from pydantic import BaseModel

from sqlalchemy.orm import Session

from domains.governance.services.auth_controller_service import get_current_user

from infrastructure.database.database import get_db

from domains.catalog.models.products import Category
from domains.country.models.countries import CountryConfig
from domains.country.models.country_enhancements import CountryCity

class CityResponse(BaseModel):
    id: int
    name: str
    region: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    population: Optional[int]

class CountryDropdownResponse(BaseModel):
    code: str
    name: str
    currency: str
    currency_symbol: Optional[str]
    phone_code: Optional[str]

class CategoryResponse(BaseModel):
    id: int
    name: str
    slug: str
    parent_id: Optional[int]

def get_cities_dropdown(country_code: str, q: Optional[str], limit: int, db: Session, _current_user: dict):
    cc = country_code.upper()
    country = db.query(CountryConfig).filter(
        CountryConfig.code == cc,
        CountryConfig.is_active == True,
    ).first()
    if not country:
        raise HTTPException(status_code=404, detail="Country not found or inactive")

    query = db.query(CountryCity).filter(
        CountryCity.country_code == cc,
        CountryCity.is_active == True,
    )
    if q:
        query = query.filter(CountryCity.name.ilike(f"%{q}%"))
    cities = query.order_by(CountryCity.population.desc().nullslast(), CountryCity.name.asc()).limit(limit).all()

    return [
        CityResponse(
            id=c.id,
            name=c.name,
            region=c.region,
            latitude=float(c.latitude) if c.latitude else None,
            longitude=float(c.longitude) if c.longitude else None,
            population=c.population,
        )
        for c in cities
    ]

def get_countries_dropdown(db: Session, _current_user: dict):
    countries = (
        db.query(CountryConfig)
        .filter(CountryConfig.is_active == True)
        .order_by(CountryConfig.name.asc())
        .all()
    )
    return [
        CountryDropdownResponse(
            code=c.code,
            name=c.name,
            currency=c.currency,
            currency_symbol=c.currency_symbol,
            phone_code=c.phone_code,
        )
        for c in countries
    ]

def get_categories_dropdown(country_code: Optional[str], parent_id: Optional[int], db: Session, _current_user: dict):
    query = db.query(Category)
    if parent_id is not None:
        query = query.filter(Category.parent_id == parent_id)
    categories = query.order_by(Category.name.asc()).all()
    return [
        CategoryResponse(
            id=c.id,
            name=c.name,
            slug=c.slug,
            parent_id=c.parent_id,
        )
        for c in categories
    ]

