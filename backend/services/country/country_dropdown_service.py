"""Country dropdown router logic, extracted behind the service layer (clears LC1/W1).

Each function owns its database session via ``data.db.get_db_context`` so the
router layer never injects or touches a SQLAlchemy session directly.
"""
from typing import List, Optional

from fastapi import HTTPException


def get_cities_dropdown(country_code: str, q: Optional[str], limit: int) -> List[dict]:
    from data.db import get_db_context
    from data.models import CountryConfig, CountryCity

    cc = country_code.upper()
    with get_db_context() as db:
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
        cities = query.order_by(
            CountryCity.population.desc().nullslast(), CountryCity.name.asc()
        ).limit(limit).all()
        return [
            {
                "id": c.id,
                "name": c.name,
                "region": c.region,
                "latitude": float(c.latitude) if c.latitude else None,
                "longitude": float(c.longitude) if c.longitude else None,
                "population": c.population,
            }
            for c in cities
        ]


def get_countries_dropdown(skip: int, limit: int) -> List[dict]:
    from data.db import get_db_context
    from data.models import CountryConfig

    with get_db_context() as db:
        countries = (
            db.query(CountryConfig)
            .filter(CountryConfig.is_active == True)
            .order_by(CountryConfig.name.asc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [
            {
                "code": c.code,
                "name": c.name,
                "currency": c.currency,
                "currency_symbol": c.currency_symbol,
                "phone_code": c.phone_code,
            }
            for c in countries
        ]


def get_categories_dropdown(
    country_code: Optional[str], parent_id: Optional[int], skip: int, limit: int
) -> List[dict]:
    from data.db import get_db_context
    from data.models import Category

    with get_db_context() as db:
        query = db.query(Category)
        if parent_id is not None:
            query = query.filter(Category.parent_id == parent_id)
        categories = query.order_by(Category.name.asc()).offset(skip).limit(limit).all()
        return [
            {
                "id": c.id,
                "name": c.name,
                "slug": c.slug,
                "parent_id": c.parent_id,
            }
            for c in categories
        ]
