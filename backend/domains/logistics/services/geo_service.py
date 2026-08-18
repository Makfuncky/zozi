"""Geo/router logic, extracted behind the service layer (clears LC1/W1).

Each function owns its database session via ``data.db.get_db_context`` so the
router layer never injects or touches a SQLAlchemy session directly.
"""
from __future__ import annotations
from typing import Optional
import structlog
logger = structlog.get_logger(__name__)


def resolve_country_from_ip(ip_address: str) -> Optional[str]:
    from infrastructure.database.database import get_db_context
    from domains.country.services.country_detection import CountryDetectionService

    with get_db_context() as db:
        service = CountryDetectionService(db)
        country_code, _ = service._lookup_country_by_ip(ip_address)
        return country_code


def get_country_details(country_code: Optional[str]) -> dict:
    from infrastructure.database.database import get_db_context
    from domains.country.models.countries import CountryConfig

    with get_db_context() as db:
        country = (
            db.query(CountryConfig).filter(CountryConfig.code == country_code).first()
            if country_code
            else None
        )
        return {
            "country_code": country_code,
            "country_name": country.name if country else None,
            "currency": country.currency if country else None,
            "currency_symbol": country.currency_symbol if country else None,
            "timezone": country.timezone if country else None,
            "language": country.language if country else None,
        }


def list_geo_countries(skip: int, limit: int) -> list:
    from infrastructure.database.database import get_db_context
    from domains.country.models.countries import CountryConfig

    with get_db_context() as db:
        countries = (
            db.query(CountryConfig)
            .filter(CountryConfig.is_active == True)
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
                "language": c.language,
                "timezone": c.timezone,
            }
            for c in countries
        ]
