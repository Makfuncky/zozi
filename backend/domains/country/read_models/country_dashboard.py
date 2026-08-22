"""CQRS-lite read models for the country domain dashboard.

Projected read-optimized views served from the sanctioned read_models/ slice
(ARCHITECTURE_DIAGRAM.md Law 3). Populated incrementally as projections are
extracted from write services.
"""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel


class CountryDashboardProjection(BaseModel):
    """Aggregated country dashboard data."""
    country_code: str
    country_name: str
    currency: str
    is_active: bool
    staff_count: int = 0
    tax_rate: Optional[float] = None
    city_count: int = 0


class CountryTaxRateProjection(BaseModel):
    """Country tax rate projection."""
    country_code: str
    tax_type: str
    tax_rate: float
    tax_name: str
    is_active: bool


def read_country_dashboard(db, country_code: str) -> Optional[CountryDashboardProjection]:
    """Read aggregated country dashboard data."""
    from domains.country.models.countries import CountryConfig
    from domains.country.models.country_enhancements import CountryStaffAssignment, CountryCity
    from sqlalchemy import func

    config = db.query(CountryConfig).filter(
        CountryConfig.code == country_code,
        CountryConfig.is_active == True
    ).first()

    if not config:
        return None

    staff_count = db.query(func.count(CountryStaffAssignment.id)).filter(
        CountryStaffAssignment.country_code == country_code,
        CountryStaffAssignment.is_active == True
    ).scalar() or 0

    city_count = db.query(func.count(CountryCity.id)).filter(
        CountryCity.country_code == country_code,
        CountryCity.is_active == True
    ).scalar() or 0

    return CountryDashboardProjection(
        country_code=config.code,
        country_name=config.name,
        currency=config.currency,
        currency_symbol=config.currency_symbol,
        is_active=config.is_active,
        staff_count=staff_count,
        tax_rate=float(config.tax_rate) if config.tax_rate else None,
        city_count=city_count,
    )
