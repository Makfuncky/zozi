"""Downstream System Auto-Wiring Service.

Integrates country configuration with downstream systems via raw SQL
against the ``country_configs`` table. Law 1 compliant: this module
does not import any domain ORM class — it reads configuration data
through the schema contract documented in ``domains/country/``.

- Payment Orchestrator: Gateway selection per country
- Treasury: Settlement hold days
- Logistics: SLA and holiday integration
- Product Moderation: Product restriction enforcement
- Cross-Border Checkout: Tax/currency/gateway resolution
"""
from __future__ import annotations

import json
import logging
from typing import Any, Optional

from sqlalchemy.orm import Session
from sqlalchemy import text


def _country_row(db: Session, country_code: str) -> Optional[dict[str, Any]]:
    """Fetch the country config row as a plain dict. Returns ``None`` if
    the country is not configured."""
    if not country_code:
        return None
    row = db.execute(
        text(
            "SELECT payment_gateways_json, settlement_hold_days, "
            "public_holidays_json, product_restrictions_json, "
            "logistics_model, commission_tiers_json, "
            "supplier_requirements_json, payout_settings_json, "
            "default_currency, tax_rate, tax_name, tax_inclusive "
            "FROM country_configs WHERE code = :code"
        ),
        {"code": country_code},
    ).mappings().first()
    return dict(row) if row else None


def get_enabled_gateways_for_country(db: Session, country_code: str) -> list[dict[str, Any]]:
    """Get list of enabled payment gateways for a country."""
    row = _country_row(db, country_code)
    if not row or not row.get("payment_gateways_json"):
        return []
    try:
        gateways = json.loads(row["payment_gateways_json"]) if isinstance(row["payment_gateways_json"], str) else row["payment_gateways_json"]
        return [g for g in (gateways or []) if g.get("enabled", True)]
    except (json.JSONDecodeError, TypeError):
        return []


def get_settlement_hold_days(db: Session, country_code: str) -> int:
    """Get settlement hold days for a country from config."""
    row = _country_row(db, country_code)
    if not row:
        return 3
    return int(row.get("settlement_hold_days") or 3)


def get_public_holidays_for_country(db: Session, country_code: str) -> list[dict[str, Any]]:
    """Get public holidays for a country."""
    row = _country_row(db, country_code)
    if not row or not row.get("public_holidays_json"):
        return []
    try:
        holidays = json.loads(row["public_holidays_json"]) if isinstance(row["public_holidays_json"], str) else row["public_holidays_json"]
        return holidays or []
    except (json.JSONDecodeError, TypeError):
        return []


def is_product_restricted_for_country(db: Session, product_id: int, country_code: str) -> bool:
    """Check if a product is restricted in a specific country."""
    row = _country_row(db, country_code)
    if not row or not row.get("product_restrictions_json"):
        return False
    try:
        restrictions = json.loads(row["product_restrictions_json"]) if isinstance(row["product_restrictions_json"], str) else row["product_restrictions_json"]
        restriction_list = restrictions or []
        product_row = db.execute(
            text("SELECT category FROM products WHERE id = :pid"),
            {"pid": product_id},
        ).first()
        if not product_row or not product_row[0]:
            return False
        return product_row[0].lower() in [r.lower() for r in restriction_list]
    except (json.JSONDecodeError, TypeError):
        return False


def get_product_restrictions_for_country(db: Session, country_code: str) -> list[str]:
    """Get product restrictions for a country."""
    row = _country_row(db, country_code)
    if not row or not row.get("product_restrictions_json"):
        return []
    try:
        restrictions = json.loads(row["product_restrictions_json"]) if isinstance(row["product_restrictions_json"], str) else row["product_restrictions_json"]
        return restrictions or []
    except (json.JSONDecodeError, TypeError):
        return []


def calculate_order_totals_with_country(
    db: Session,
    subtotal: Any,
    country_code: str,
    coupon_code: Optional[str] = None,
    items: Optional[list[dict]] = None,
) -> dict[str, Any]:
    """Calculate order totals with country-specific tax and currency.

    Tax/currency resolution is performed against the ``country_configs``
    schema contract (no domain ORM imports). Coupon handling stays
    infrastructure-level (caller-side validation).
    """
    from kernel.money import to_decimal

    subtotal_decimal = to_decimal(subtotal)
    row = _country_row(db, country_code)
    default_currency = (row or {}).get("default_currency") or "USD"
    tax_rate = float((row or {}).get("tax_rate") or 0)
    tax_name = (row or {}).get("tax_name") or "Tax"
    is_inclusive = bool((row or {}).get("tax_inclusive"))

    net_amount = float(subtotal_decimal)
    if is_inclusive:
        tax_amount = round(net_amount - net_amount / (1 + tax_rate), 2)
    else:
        tax_amount = round(net_amount * tax_rate, 2)
    total_amount = round(net_amount + (0 if is_inclusive else tax_amount), 2)

    return {
        "country_code": country_code,
        "currency": default_currency,
        "tax_type": "VAT",
        "tax_name": tax_name,
        "tax_rate": tax_rate,
        "tax_amount": tax_amount,
        "vat_amount": tax_amount,
        "net_amount": net_amount,
        "total_amount": total_amount,
        "is_inclusive": is_inclusive,
    }


def get_checkout_payment_config(db: Session, country_code: str, payment_method: str) -> dict[str, Any]:
    """Get payment configuration for checkout."""
    gateways = get_enabled_gateways_for_country(db, country_code)
    gateway_code = None
    for gw in gateways:
        gw_id = str(gw.get("gateway_id", "")).lower()
        if payment_method.lower() in gw_id or gw_id in payment_method.lower():
            gateway_code = gw.get("gateway_id")
            break
    if not gateway_code and gateways:
        gateway_code = gateways[0].get("gateway_id")

    return {
        "country_code": country_code,
        "payment_method": payment_method,
        "gateway_code": gateway_code,
        "available_gateways": [g.get("gateway_id") for g in gateways],
        "supports_cod": any(g.get("gateway_id", "").lower() == "cod" for g in gateways) or payment_method.lower() == "cod",
    }


def get_logistics_sla_for_country(db: Session, country_code: str) -> dict[str, Any]:
    """Get logistics SLA configuration for a country."""
    row = _country_row(db, country_code)
    if not row:
        return {"min_days": 1, "max_days": 7, "holidays": []}

    holidays = get_public_holidays_for_country(db, country_code)

    return {
        "min_days": 1,
        "max_days": 7,
        "holidays": holidays,
        "logistics_model": row.get("logistics_model") or "basic_delivery",
    }


def get_commission_tiers_for_country(db: Session, country_code: str) -> list[dict[str, Any]]:
    """Get commission tiers for a country."""
    row = _country_row(db, country_code)
    if not row or not row.get("commission_tiers_json"):
        return []
    try:
        tiers = json.loads(row["commission_tiers_json"]) if isinstance(row["commission_tiers_json"], str) else row["commission_tiers_json"]
        return tiers or []
    except (json.JSONDecodeError, TypeError):
        return []


def get_supplier_requirements_for_country(db: Session, country_code: str) -> dict[str, Any]:
    """Get supplier requirements for a country."""
    row = _country_row(db, country_code)
    if not row or not row.get("supplier_requirements_json"):
        return {"kyc_level": "standard", "required_documents": [], "approval_required": True}
    try:
        reqs = json.loads(row["supplier_requirements_json"]) if isinstance(row["supplier_requirements_json"], str) else row["supplier_requirements_json"]
        return reqs or {}
    except (json.JSONDecodeError, TypeError):
        return {"kyc_level": "standard", "required_documents": [], "approval_required": True}


def get_payout_settings_for_country(db: Session, country_code: str) -> dict[str, Any]:
    """Get payout settings for a country."""
    row = _country_row(db, country_code)
    if not row or not row.get("payout_settings_json"):
        return {"minimum_payout_amount": 100.0, "payout_schedule": "weekly", "payout_day": "sunday"}
    try:
        settings = json.loads(row["payout_settings_json"]) if isinstance(row["payout_settings_json"], str) else row["payout_settings_json"]
        return settings or {}
    except (json.JSONDecodeError, TypeError):
        return {"minimum_payout_amount": 100.0, "payout_schedule": "weekly", "payout_day": "sunday"}

