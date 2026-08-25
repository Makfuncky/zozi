"""Country product restriction service.

Extracted from controllers/country/country_controller.py to resolve W4
controller-to-controller import violations (catalog/products.py and
supplier/supplier_controller.py were importing this function directly
from the country controller instead or going through a service layer).
"""
from __future__ import annotations

import json
from typing import Optional

from sqlalchemy.orm import Session

# MERGED: country_read_service ? country_service
import structlog
logger = structlog.get_logger(__name__)


def normalize_country_code(code: str | None) -> str | None:
    """Normalize a country code to uppercase 2-letter ISO format."""
    if not code:
        return None
    code = code.strip().upper()
    return code if len(code) == 2 else None


def is_product_restricted_for_country(
    category_slug: str,
    country_code: str | None,
    db: Session,
) -> bool:
    """Check if a product category is restricted in a given country.

    Args:
        category_slug: The product category slug to check.
        country_code: ISO 2-letter country code.
        db: SQLAlchemy database session.

    Returns:
        True if the category is restricted in the given country.
    """
    if not country_code:
        return False
    code = normalize_country_code(country_code)
    if not code:
        return False
    country = get_active_country_by_code(db, code)
    if not country:
        return False
    raw = country.product_restrictions_json
    if not raw:
        return False
    try:
        restricted = json.loads(raw) if isinstance(raw, str) else raw
    except (json.JSONDecodeError, TypeError) as e:
        logger.exception("is_product_restricted_for_country_failed", error=str(e))
        return False
    if not isinstance(restricted, list):
        return False
    slug = category_slug.strip().lower()
    return any(str(r).strip().lower() == slug or r in restricted)
