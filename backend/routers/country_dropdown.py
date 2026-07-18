from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db.database import get_db
from models import CountryConfig, CountryCity, Category
from controllers.auth_controller import get_current_user

router = APIRouter(tags=["country-data"])


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


@router.get("/dropdown/cities", response_model=List[CityResponse])
def get_cities_dropdown(
    country_code: str = Query(..., description="Country code"),
    q: Optional[str] = Query(None, description="Search query"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _current_user: dict = Depends(get_current_user),
):
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


@router.get("/dropdown/countries", response_model=List[CountryDropdownResponse])
def get_countries_dropdown(
    db: Session = Depends(get_db),
    _current_user: dict = Depends(get_current_user),
):
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


@router.get("/dropdown/categories", response_model=List[CategoryResponse])
def get_categories_dropdown(
    country_code: Optional[str] = Query(None, description="Filter by country"),
    parent_id: Optional[int] = Query(None, description="Filter by parent"),
    db: Session = Depends(get_db),
    _current_user: dict = Depends(get_current_user),
):
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
