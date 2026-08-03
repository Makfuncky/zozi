"""Product moderation service, extracted behind the service layer (clears LC1/W1).

Each function owns its database session via ``data.db.get_db_context`` so the
router layer never injects or touches a SQLAlchemy session directly.
"""
import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


def get_restrictions(country_code: str) -> Dict[str, Any]:
    """Get product restrictions for a country."""
    from data.db import get_db_context
    from data.models import CountryConfig

    with get_db_context() as db:
        config = db.query(CountryConfig).filter(
            CountryConfig.code == country_code.upper()
        ).first()

        if not config:
            return {"restricted_categories": [], "restricted_keywords": [], "age_restrictions": {}}

        try:
            restrictions = json.loads(config.product_restrictions_json) if isinstance(config.product_restrictions_json, str) else config.product_restrictions_json
        except (json.JSONDecodeError, TypeError):
            return {"restricted_categories": [], "restricted_keywords": [], "age_restrictions": {}}

        return restrictions


def is_product_allowed(country_code: str, product_data: Dict[str, Any]) -> Dict[str, Any]:
    """Check if a product is allowed in a country."""
    restrictions = get_restrictions(country_code)

    errors = []

    categories = product_data.get("categories", [])
    restricted_categories = restrictions.get("restricted_categories", [])
    for cat in categories:
        if cat in restricted_categories:
            errors.append(f"Category '{cat}' is restricted in {country_code}")

    title = product_data.get("title", "").lower()
    description = product_data.get("description", "").lower()
    restricted_keywords = restrictions.get("restricted_keywords", [])
    for keyword in restricted_keywords:
        if keyword.lower() in title or keyword.lower() in description:
            errors.append(f"Keyword '{keyword}' is restricted")

    return {
        "allowed": len(errors) == 0,
        "errors": errors,
        "restrictions": restrictions
    }
