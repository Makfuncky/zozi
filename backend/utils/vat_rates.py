"""
Curated VAT / sales-tax rates per country — used as fallback when the
external VAT API is unavailable.

``VAT_RATES`` stores the standard VAT percentage (e.g. 5 = 5 %).
``LEGAL_DEFAULTS`` stores per-country legal rule overrides such as
minimum order age, return windows, and product restrictions.

Add entries here as new countries are onboarded.
"""

from typing import Any, Optional

VAT_RATES: dict[str, float] = {
    "SA": 15.0,
    "AE": 5.0,
    "OM": 5.0,
    "BH": 5.0,
    "KW": 5.0,
    "QA": 0.0,
    "US": 0.0,
    "GB": 20.0,
    "DE": 19.0,
    "FR": 20.0,
    "IT": 22.0,
    "ES": 21.0,
    "PK": 18.0,
    "IN": 18.0,
}

LEGAL_DEFAULTS: dict[str, dict[str, Any]] = {
    "SA": {
        "minimum_order_age": 18,
        "max_returns_allowed": 3,
        "return_window_days": 14,
        "refund_processing_days": 7,
        "requires_commercial_license": True,
        "requires_vat_registration": True,
        "product_restrictions": ["alcohol", "pork", "gambling_related"],
    },
    "OM": {
        "minimum_order_age": 18,
        "max_returns_allowed": 3,
        "return_window_days": 10,
        "refund_processing_days": 5,
        "requires_commercial_license": True,
        "requires_vat_registration": True,
        "product_restrictions": ["alcohol", "pork"],
    },
}


def get_vat_rate(country_code: str) -> Optional[float]:
    """Return the standard VAT/sales-tax percentage for *country_code*, or ``None``.

    Example: ``get_vat_rate("SA")`` → ``15.0`` (15%).
    """
    return VAT_RATES.get(country_code.upper())


def get_legal_defaults(country_code: str) -> dict[str, Any]:
    """Return legal rule defaults for *country_code*, falling back to a sensible
    empty dict when no curated entry exists."""
    return LEGAL_DEFAULTS.get(country_code.upper(), {})