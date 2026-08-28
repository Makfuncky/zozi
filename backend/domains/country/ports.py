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

from domains.country.models.countries import CountryConfig, CountryGatewayCredentials, PayoutRuleCategory, PayoutRuleProduct
from domains.country.models.country_control import PaymentOrchestratorSync, SupplierOnboardingSync
from domains.country.models.country_enhancements import CountryCategoryTaxRate, CountryCity
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


def country_city_query(db: Session) -> object:
    """Return a base ``CountryCity`` query for sanctioned cross-domain delegation."""
    return db.query(CountryCity)


def country_communication_query(db: Session) -> object:
    """Return a base ``CountryCommunication`` query for sanctioned cross-domain delegation."""
    from domains.country.models.countries import CountryCommunication
    return db.query(CountryCommunication)


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

# --- Lazy service exports (Law 3 sanctioned cross-domain surface) ---
# Cross-domain consumers import these from ports instead of reaching
# into the services tree directly.
_LAZY_SERVICE_EXPORTS: dict[str, tuple[str, str]] = {
    "add_country_city": ("domains.country.services.core.country_config_admin_service", "add_country_city"),
    "archive_country": ("domains.country.services.core.country_config_admin_service", "archive_country"),
    "bulk_archive_countries": ("domains.country.services.core.country_config_admin_service", "bulk_archive_countries"),
    "bulk_restore_countries": ("domains.country.services.core.country_config_admin_service", "bulk_restore_countries"),
    "create_country_commission_rate": ("domains.country.services.core.country_config_admin_service", "create_country_commission_rate"),
    "create_feature_flag": ("domains.country.services.core.country_config_admin_service", "create_feature_flag"),
    "delete_country_city": ("domains.country.services.core.country_config_admin_service", "delete_country_city"),
    "delete_country_commission_rate": ("domains.country.services.core.country_config_admin_service", "delete_country_commission_rate"),
    "delete_feature_flag": ("domains.country.services.core.country_config_admin_service", "delete_feature_flag"),
    "hard_delete_country": ("domains.country.services.core.country_config_admin_service", "hard_delete_country"),
    "list_country_commission_rates": ("domains.country.services.core.country_config_admin_service", "list_country_commission_rates"),
    "patch_country_city": ("domains.country.services.core.country_config_admin_service", "patch_country_city"),
    "restore_country": ("domains.country.services.core.country_config_admin_service", "restore_country"),
    "toggle_country_active": ("domains.country.services.core.country_config_admin_service", "toggle_country_active"),
    "update_feature_flag": ("domains.country.services.core.country_config_admin_service", "update_feature_flag"),
    "CountryDetectionService": ("domains.country.services.geo.country_detection", "CountryDetectionService"),
    "is_rtl_language": ("domains.country.services.localization.localization_service", "is_rtl_language"),
    "GATEWAY_REGISTRY": ("domains.country.services.research.country_auto_populate", "GATEWAY_REGISTRY"),
    "is_product_restricted_for_country": ("domains.country.services.restriction.country_restriction_service", "is_product_restricted_for_country"),
    "add_city": ("domains.country.services.staff.country_admin_write_service", "add_city"),
    "assign_staff": ("domains.country.services.staff.country_admin_write_service", "assign_staff"),
    "delete_city": ("domains.country.services.staff.country_admin_write_service", "delete_city"),
    "list_cities": ("domains.country.services.staff.country_admin_write_service", "list_cities"),
    "list_communications": ("domains.country.services.staff.country_admin_write_service", "list_communications"),
    "list_staff": ("domains.country.services.staff.country_admin_write_service", "list_staff"),
    "list_tax_rates": ("domains.country.services.staff.country_admin_write_service", "list_tax_rates"),
    "mark_communication_read": ("domains.country.services.staff.country_admin_write_service", "mark_communication_read"),
    "remove_staff": ("domains.country.services.staff.country_admin_write_service", "remove_staff"),
    "send_country_communication": ("domains.country.services.staff.country_admin_write_service", "send_country_communication"),
    "set_tax_rate": ("domains.country.services.staff.country_admin_write_service", "set_tax_rate"),
    "update_city": ("domains.country.services.staff.country_admin_write_service", "update_city"),
    "CountryGatewayCredentials": ("domains.country.models.countries", "CountryGatewayCredentials"),
    "PayoutRuleCategory": ("domains.country.models.countries", "PayoutRuleCategory"),
    "PayoutRuleProduct": ("domains.country.models.countries", "PayoutRuleProduct"),
    "PaymentOrchestratorSync": ("domains.country.models.country_control", "PaymentOrchestratorSync"),
}
import importlib


def __getattr__(name: str):
    if name in _LAZY_SERVICE_EXPORTS:
        module_path, symbol = _LAZY_SERVICE_EXPORTS[name]
        mod = importlib.import_module(module_path)
        value = getattr(mod, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


# --- Query delegation (Law 3 sanctioned cross-domain query surface) ---

def country_gateway_credentials_query(db: Session) -> object:
    """Return a base ``CountryGatewayCredentials`` query for sanctioned cross-domain delegation."""
    return db.query(CountryGatewayCredentials)


def payout_rule_category_query(db: Session) -> object:
    """Return a base ``PayoutRuleCategory`` query for sanctioned cross-domain delegation."""
    return db.query(PayoutRuleCategory)


def payout_rule_product_query(db: Session) -> object:
    """Return a base ``PayoutRuleProduct`` query for sanctioned cross-domain delegation."""
    return db.query(PayoutRuleProduct)


def payment_orchestrator_sync_query(db: Session) -> object:
    """Return a base ``PaymentOrchestratorSync`` query for sanctioned cross-domain delegation."""
    return db.query(PaymentOrchestratorSync)

