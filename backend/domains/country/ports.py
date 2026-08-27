"""Country domain — sanctioned cross-domain READ surface (ports).

Per ARCHITECTURE_DIAGRAM.md Law 3, cross-domain *reads* may ONLY happen through a
publishing domain's ``ports.py``. Other domains import these functions instead of
importing ``domains.country.models`` or ``domains.country.services`` directly.

These are pure read helpers: no writes, no business decisions, no permission
checks (callers remain responsible for feature gating via ``rbac``).

IMPORTANT: This module must NOT import from ``domains.country.services`` to avoid
circular imports. Services import from ports, so ports cannot import from services.
Service functions are imported directly from their service modules by callers.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Optional

from sqlalchemy.orm import Session

from domains.country.models.countries import CountryConfig
from domains.country.models.country_enhancements import CountryCategoryTaxRate
from domains.country.utils.country_rls import get_country_or_404


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
    """Resolve the effective tax rate for a category in a country."""
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


def country_config_query(db: Session) -> object:
    """Return a base ``CountryConfig`` query for sanctioned cross-domain delegation."""
    return db.query(CountryConfig)


def normalize_country_code(code: str) -> str:
    """Normalize a country code to uppercase 3-letter format."""
    if not code:
        return ""
    return str(code).strip().upper()


def calculate_tax_for_country(amount: Decimal, country_code: str, db: Session,
                              category: str | None = None, inclusive: bool | None = None) -> dict:
    """Calculate tax via finance ports (Law 3)."""
    from domains.finance.ports import calculate_tax as _calc
    return _calc(amount, country_code, db, category=category, inclusive=inclusive)


def translate_text(text: str, source_lang: str = "en", target_lang: str = "ar") -> dict:
    """Sanctioned cross-domain read: translate text between languages."""
    from domains.country.services.localization.localization_service import translate_text as _svc
    return _svc(text, source_lang, target_lang)


def format_currency(amount: float, currency_code: str = "USD", locale: str = "en") -> dict:
    """Sanctioned cross-domain read: format currency for locale."""
    from domains.country.services.localization.localization_service import format_currency as _svc
    return _svc(amount, currency_code, locale)
