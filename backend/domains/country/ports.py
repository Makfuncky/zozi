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


# --- Country-specific function re-exports (used by governance and other domains) ---
# These functions are named with a ``country_`` prefix to avoid name collisions.
# They delegate to the canonical service functions, imported lazily to avoid
# circular imports (services import from ports, so ports cannot eagerly import from services).

def country_add_city(db: Session, country_code: str, **kwargs):
    """Add a city to a country."""
    from domains.country.services.country_audit_admin_service import add_city
    return add_city(db, country_code, **kwargs)

def country_assign_staff(db: Session, country_code: str, **kwargs):
    """Assign staff to a country."""
    from domains.country.services.country_audit_admin_service import assign_staff
    return assign_staff(db, country_code, **kwargs)

def country_delete_city(db: Session, country_code: str, **kwargs):
    """Delete a city from a country."""
    from domains.country.services.country_audit_admin_service import delete_city
    return delete_city(db, country_code, **kwargs)

def country_list_cities(db: Session, country_code: str, **kwargs):
    """List cities in a country."""
    from domains.country.services.country_audit_admin_service import list_cities
    return list_cities(db, country_code, **kwargs)

def country_list_communications(db: Session, country_code: str, **kwargs):
    """List communications for a country."""
    from domains.country.services.country_audit_admin_service import list_communications
    return list_communications(db, country_code, **kwargs)

def country_list_staff(db: Session, country_code: str, **kwargs):
    """List staff assigned to a country."""
    from domains.country.services.country_audit_admin_service import list_staff
    return list_staff(db, country_code, **kwargs)

def country_list_tax_rates(db: Session, country_code: str, **kwargs):
    """List tax rates for a country."""
    from domains.country.services.country_audit_admin_service import list_tax_rates
    return list_tax_rates(db, country_code, **kwargs)

def country_mark_communication_read(db: Session, country_code: str, **kwargs):
    """Mark a communication as read."""
    from domains.country.services.country_audit_admin_service import mark_communication_read
    return mark_communication_read(db, country_code, **kwargs)

def country_remove_staff(db: Session, country_code: str, **kwargs):
    """Remove staff from a country."""
    from domains.country.services.country_audit_admin_service import remove_staff
    return remove_staff(db, country_code, **kwargs)

def country_send_country_communication(db: Session, country_code: str, **kwargs):
    """Send a communication to country staff."""
    from domains.country.services.country_audit_admin_service import send_country_communication
    return send_country_communication(db, country_code, **kwargs)

def country_set_tax_rate(db: Session, country_code: str, **kwargs):
    """Set a tax rate for a country."""
    from domains.country.services.country_audit_admin_service import set_tax_rate
    return set_tax_rate(db, country_code, **kwargs)

def country_update_city(db: Session, country_code: str, **kwargs):
    """Update a city in a country."""
    from domains.country.services.country_audit_admin_service import update_city
    return update_city(db, country_code, **kwargs)
