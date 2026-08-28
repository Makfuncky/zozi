"""Country dropdown router logic, extracted behind the service layer (clears LC1/W1).

Each function owns its database session via ``data.db.get_db_context`` so the
router layer never injects or touches a SQLAlchemy session directly.
"""
from __future__ import annotations
from typing import List, Optional

from fastapi import HTTPException
import structlog
logger = structlog.get_logger(__name__)


def get_cities_dropdown(country_code: str, q: Optional[str], limit: int) -> List[dict]:
    from infrastructure.database.database import get_db_context
    from domains.country.models.countries import CountryConfig
    from domains.country.models.country_enhancements import CountryCity

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


def get_countries_dropdown(limit: int = 20, cursor: Optional[str] = None) -> dict:
    from infrastructure.database.database import get_db_context
    from domains.country.models.countries import CountryConfig
    from infrastructure.utils.pagination import cursor_paginate_asc, build_cursor_pagination_payload

    with get_db_context() as db:
        query = (
            db.query(CountryConfig)
            .filter(CountryConfig.is_active == True)
            .order_by(CountryConfig.id.asc())
        )
        result = cursor_paginate_asc(
            query,
            cursor=cursor,
            page_size=limit,
            serializer=lambda c: {
                "code": c.code,
                "name": c.name,
                "currency": c.currency,
                "currency_symbol": c.currency_symbol,
                "phone_code": c.phone_code,
            },
        )
        return build_cursor_pagination_payload(result.items, result.next_cursor, result.page_size)


def get_categories_dropdown(
    country_code: Optional[str], parent_id: Optional[int], limit: int = 20, cursor: Optional[str] = None
) -> dict:
    from infrastructure.database.database import get_db_context
    from domains.catalog.ports import Category
    from infrastructure.utils.pagination import cursor_paginate_asc, build_cursor_pagination_payload

    with get_db_context() as db:
        query = db.query(Category)
        if parent_id is not None:
            query = query.filter(Category.parent_id == parent_id)
        query = query.order_by(Category.id.asc())
        result = cursor_paginate_asc(
            query,
            cursor=cursor,
            page_size=limit,
            serializer=lambda c: {
                "id": c.id,
                "name": c.name,
                "slug": c.slug,
                "parent_id": c.parent_id,
            },
        )
        return build_cursor_pagination_payload(result.items, result.next_cursor, result.page_size)
