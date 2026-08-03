"""
Curated per-category tax profiles — used to look up category-specific
tax rates or exemptions for a given country.

Some countries apply reduced VAT rates (or exemptions) to specific
product categories (e.g. 5 % on food in SA, 0 % on books).  This
module provides those overrides so the auto-populate engine can
apply them during country configuration.
"""
from __future__ import annotations

from typing import Any, Optional

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


def get_category_tax_profile(country_code: str) -> dict[str, Any]:
    """Return the curated category-tax profile for *country_code*, or an empty
    dict if no curated profile exists.

    The caller is expected to merge this data with the platform-wide defaults.
    """
    return CATEGORY_TAX_PROFILES.get(country_code.upper(), {})