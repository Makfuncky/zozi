from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from data.dependencies_auth import get_current_user
from data.services_country_dropdown_service import (
    get_cities_dropdown,
    get_countries_dropdown,
    get_categories_dropdown,
)

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
def get_cities_dropdown_endpoint(
    country_code: str = Query(..., description="Country code"),
    q: Optional[str] = Query(None, description="Search query"),
    limit: int = Query(50, ge=1, le=200),
    _current_user: dict = Depends(get_current_user),
):
    return get_cities_dropdown(country_code, q, limit)


@router.get("/dropdown/countries", response_model=List[CountryDropdownResponse])
def get_countries_dropdown_endpoint(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    _current_user: dict = Depends(get_current_user),
):
    return get_countries_dropdown(skip, limit)


@router.get("/dropdown/categories", response_model=List[CategoryResponse])
def get_categories_dropdown_endpoint(
    country_code: Optional[str] = Query(None, description="Filter by country"),
    parent_id: Optional[int] = Query(None, description="Filter by parent"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    _current_user: dict = Depends(get_current_user),
):
    return get_categories_dropdown(country_code, parent_id, skip, limit)
