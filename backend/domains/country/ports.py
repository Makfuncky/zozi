"""Country domain — sanctioned cross-domain READ surface (ports).

Per NEW_STRUCTURE.md Law 3, cross-domain *reads* may ONLY happen through a
publishing domain's ``ports.py``. Other domains import these functions instead of
importing ``domains.country.models`` or ``domains.country.services`` directly.

These are pure read helpers: no writes, no business decisions, no permission
checks (callers remain responsible for feature gating via ``rbac``).
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from domains.country.models.countries import CountryConfig
from domains.country.models.country_enhancements import CountryCategoryTaxRate


def get_country_config(db: Session, country_code: str) -> Optional[CountryConfig]:
    """Return the active CountryConfig for ``country_code`` (or None)."""
    cc = country_code.strip().upper()
    return (
        db.query(CountryConfig)
        .filter(CountryConfig.code == cc, CountryConfig.is_active == True)  # noqa: E712
        .first()
    )


def get_country_currency(db: Session, country_code: str) -> Optional[str]:
    cfg = get_country_config(db, country_code)
    return cfg.currency if cfg else None


def is_product_restricted_for_country(db: Session, country_code: str, product_id: int) -> bool:
    """True if the product is in the country's product_restrictions list."""
    cfg = get_country_config(db, country_code)
    if not cfg or not cfg.product_restrictions_json:
        return False
    import json

    try:
        restricted = json.loads(cfg.product_restrictions_json) or []
    except (ValueError, TypeError):
        return False
    return product_id in restricted


def get_tax_rate_for_category(
    db: Session, country_code: str, category_id: int
) -> Optional[Decimal]:
    """Resolve the effective tax rate for a category in a country.

    Falls back to the country's base tax rate when no category-specific rate exists.
    """
    cc = country_code.strip().upper()
    row = (
        db.query(CountryCategoryTaxRate)
        .filter(
            CountryCategoryTaxRate.country_code == cc,
            CountryCategoryTaxRate.category_id == category_id,
            CountryCategoryTaxRate.is_active == True,  # noqa: E712
        )
        .first()
    )
    if row and row.tax_rate is not None:
        return Decimal(str(row.tax_rate))
    cfg = get_country_config(db, country_code)
    return Decimal(str(cfg.tax_rate)) if cfg and cfg.tax_rate is not None else None


def list_active_country_codes(db: Session) -> list[str]:
    return [
        c.code
        for c in db.query(CountryConfig.code)
        .filter(CountryConfig.is_active == True)  # noqa: E712
        .order_by(CountryConfig.name.asc())
        .all()
    ]
