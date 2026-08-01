"""
Country product restriction service — checks product category restrictions per country.

This service provides the proper layer for checking whether a product category
is restricted in a given country, breaking controller-to-controller dependencies.
"""
import json
from typing import Optional

from sqlalchemy.orm import Session

from models import CountryConfig


def is_product_restricted_for_country(
    category_slug: str,
    country_code: Optional[str],
    db: Session,
) -> bool:
    """Check if a product category is restricted in a given country."""
    if not country_code:
        return False
    
    from services.logistics.logistics_partner_pricing import normalize_country_code
    code = normalize_country_code(country_code)
    if not code:
        return False
    
    country = db.query(CountryConfig).filter(
        CountryConfig.code == code,
        CountryConfig.is_active == True,
    ).first()
    if not country:
        return False
    
    raw = country.product_restrictions_json
    if not raw:
        return False
    
    try:
        restricted = json.loads(raw) if isinstance(raw, str) else raw
    except (json.JSONDecodeError, TypeError):
        return False
    
    if not isinstance(restricted, list):
        return False
    
    slug = category_slug.strip().lower()
    return any(str(r).strip().lower() == slug for r in restricted)