"""Country-level product moderation rules (LAYER 4).

Extracted from ``routers/product_moderation.py``, which previously declared a
full ``ProductModerationService`` class inside a Layer 2 router — business
logic and a ``db.query`` in the routing layer (audit LC1).

The rules come from ``country.country_configs.product_restrictions_json`` and
answer one question: *may this product be listed in this country?*
"""
from __future__ import annotations

import json
import logging
from typing import Any, Iterable, Mapping

from sqlalchemy.orm import Session

from domains.country.models.countries import CountryConfig
import structlog
logger = structlog.get_logger(__name__)

logger = logging.getLogger(__name__)

__all__ = [
    "EMPTY_RESTRICTIONS",
    "get_restrictions",
    "evaluate_product",
]


def EMPTY_RESTRICTIONS() -> dict[str, Any]:  # noqa: N802 - factory, kept callable
    """Return a fresh, empty restriction set.

    A factory (not a module-level dict) so a caller mutating the result can
    never poison the default for every other request.
    """
    return {
        "restricted_categories": [],
        "restricted_keywords": [],
        "age_restrictions": {},
    }


def get_restrictions(db: Session, country_code: str) -> dict[str, Any]:
    """Load the product restriction rules configured for a country.

    Returns an empty rule set when the country is unknown or its stored JSON is
    malformed. The malformed case is logged rather than silently swallowed
    (audit HL302).
    """
    config = (
        db.query(CountryConfig)
        .filter(CountryConfig.code == country_code.upper())
        .first()
    )
    if config is None:
        return EMPTY_RESTRICTIONS()

    raw = config.product_restrictions_json
    if raw is None:
        return EMPTY_RESTRICTIONS()
    if isinstance(raw, Mapping):
        return dict(raw)

    try:
        parsed = json.loads(raw)
    except (json.JSONDecodeError, TypeError, ValueError):
        logger.warning(
            "product_moderation.invalid_restrictions_json country=%s",
            country_code.upper(),
        )
        return EMPTY_RESTRICTIONS()

    if not isinstance(parsed, Mapping):
        logger.warning(
            "product_moderation.restrictions_not_object country=%s type=%s",
            country_code.upper(),
            type(parsed).__name__,
        )
        return EMPTY_RESTRICTIONS()
    return dict(parsed)


def evaluate_product(
    db: Session,
    country_code: str,
    product_data: Mapping[str, Any],
) -> dict[str, Any]:
    """Check a product payload against a country's restrictions.

    Returns:
        ``{"allowed": bool, "errors": list[str], "restrictions": dict}``
    """
    restrictions = get_restrictions(db, country_code)
    errors: list[str] = []

    restricted_categories = {
        str(c).lower() for c in restrictions.get("restricted_categories") or []
    }
    categories: Iterable[Any] = product_data.get("categories") or []
    for category in categories:
        if str(category).lower() in restricted_categories:
            errors.append(
                f"Category '{category}' is restricted in {country_code.upper()}"
            )

    haystack = " ".join(
        str(product_data.get(field) or "").lower()
        for field in ("title", "name", "description")
    )
    for keyword in restrictions.get("restricted_keywords") or []:
        if keyword and str(keyword).lower() in haystack:
            errors.append(f"Keyword '{keyword}' is restricted")

    return {
        "allowed": not errors,
        "errors": errors,
        "restrictions": restrictions,
    }
