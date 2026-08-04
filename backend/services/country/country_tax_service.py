"""Service methods for country category tax rates."""
from typing import List
from sqlalchemy.orm import Session
from data.models import CountryCategoryTaxRate


def get_country_category_tax_rates(db: Session, country_code: str) -> list[CountryCategoryTaxRate]:
    """Get tax rates for a country."""
    return db.query(CountryCategoryTaxRate).filter(
        CountryCategoryTaxRate.country_code == country_code
    ).all()


def get_country_category_tax_rate_by_id(db: Session, tax_rate_id: int) -> CountryCategoryTaxRate | None:
    """Get a tax rate by ID."""
    return db.query(CountryCategoryTaxRate).filter(
        CountryCategoryTaxRate.id == tax_rate_id
    ).first()


def list_active_category_tax_rates(
    db: Session, country_code: str, skip: int = 0, limit: int = 20
) -> list[CountryCategoryTaxRate]:
    """List active category tax rates for a country (delegated read for routers)."""
    return (
        db.query(CountryCategoryTaxRate)
        .filter(
            CountryCategoryTaxRate.country_code == country_code.upper(),
            CountryCategoryTaxRate.is_active == True,
        )
        .offset(skip)
        .limit(limit)
        .all()
    )


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
