"""Service methods for country category tax rates."""
from __future__ import annotations
from typing import List
from sqlalchemy.orm import Session
from domains.country.models.country_enhancements import CountryCategoryTaxRate
from infrastructure.utils.pagination import SAFE_QUERY_LIMIT
import structlog
logger = structlog.get_logger(__name__)


def get_country_category_tax_rates(db: Session, country_code: str) -> list[CountryCategoryTaxRate]:
    """Get tax rates for a country."""
    return db.query(CountryCategoryTaxRate).filter(
        CountryCategoryTaxRate.country_code == country_code
    ).limit(SAFE_QUERY_LIMIT).all()


def get_country_category_tax_rate_by_id(db: Session, tax_rate_id: int) -> CountryCategoryTaxRate | None:
    """Get a tax rate by ID."""
    return db.query(CountryCategoryTaxRate).filter(
        CountryCategoryTaxRate.id == tax_rate_id
    ).first()


def list_active_category_tax_rates(
    db: Session, country_code: str, limit: int = 20, cursor: str | None = None
) -> dict:
    """List active category tax rates for a country (cursor-paginated)."""
    from infrastructure.utils.pagination import cursor_paginate_asc, build_cursor_pagination_payload

    query = (
        db.query(CountryCategoryTaxRate)
        .filter(
            CountryCategoryTaxRate.country_code == country_code.upper(),
            CountryCategoryTaxRate.is_active == True,
        )
        .order_by(CountryCategoryTaxRate.id.asc())
    )
    result = cursor_paginate_asc(
        query,
        cursor=cursor,
        page_size=limit,
        serializer=lambda r: {
            "id": r.id,
            "category_id": r.category_id,
            "tax_rate": float(r.tax_rate),
            "tax_name": r.tax_name,
        },
    )
    return build_cursor_pagination_payload(result.items, result.next_cursor, result.page_size)


def get_category_tax_rate(
    db: Session, country_code: str, category_id: int
) -> CountryCategoryTaxRate | None:
    """Get a category tax rate by country and category (delegated read)."""
    return (
        db.query(CountryCategoryTaxRate)
        .filter(
            CountryCategoryTaxRate.country_code == country_code.upper(),
            CountryCategoryTaxRate.category_id == category_id,
        )
        .first()
    )

# === Merged from category_tax_profiles.py ===
CATEGORY_TAX_PROFILES: dict[str, dict[str, float | None]] = {
    "SA": {
        "food_beverages": 15.0,
        "medical": 0.0,
        "education": 0.0,
        "books_media": 0.0,
        "real_estate": 15.0,
        "transportation": 15.0,
        "agriculture": None,
    },
    "AE": {
        "food_beverages": 5.0,
        "medical": 0.0,
        "education": 0.0,
        "local_transport": 5.0,
        "international_transport": 0.0,
    },
    "OM": {
        "food_beverages": 5.0,
        "medical": 0.0,
        "education": 0.0,
    },
}

def get_category_tax_profile(country_code: str, category_slug: str) -> float | None:
    """Get category-specific tax rate for a country."""
    return CATEGORY_TAX_PROFILES.get(country_code, {}).get(category_slug)
