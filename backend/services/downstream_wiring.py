"""Downstream System Auto-Wiring Service.

This service integrates country configuration with downstream systems:
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

from models import CountryConfig, Order, Product
from services.tax_service import calculate_tax, get_country_config
from utils.money import to_decimal

logger = logging.getLogger(__name__)


def get_enabled_gateways_for_country(db: Session, country_code: str) -> list[dict[str, Any]]:
    """Get list of enabled payment gateways for a country."""
    config = get_country_config(db, country_code)
    if not config or not config.payment_gateways_json:
        return []
    try:
        gateways = json.loads(config.payment_gateways_json) if isinstance(config.payment_gateways_json, str) else config.payment_gateways_json
        return [g for g in (gateways or []) if g.get("enabled", True)]
    except (json.JSONDecodeError, TypeError):
        return []


def get_settlement_hold_days(db: Session, country_code: str) -> int:
    """Get settlement hold days for a country from config."""
    config = get_country_config(db, country_code)
    if not config:
        return 3
    return config.settlement_hold_days or 3


def get_public_holidays_for_country(db: Session, country_code: str) -> list[dict[str, Any]]:
    """Get public holidays for a country."""
    config = get_country_config(db, country_code)
    if not config or not config.public_holidays_json:
        return []
    try:
        holidays = json.loads(config.public_holidays_json) if isinstance(config.public_holidays_json, str) else config.public_holidays_json
        return holidays or []
    except (json.JSONDecodeError, TypeError):
        return []


def is_product_restricted_for_country(db: Session, product_id: int, country_code: str) -> bool:
    """Check if a product is restricted in a specific country."""
    config = get_country_config(db, country_code)
    if not config or not config.product_restrictions_json:
        return False
    try:
        restrictions = json.loads(config.product_restrictions_json) if isinstance(config.product_restrictions_json, str) else config.product_restrictions_json
        restriction_list = restrictions or []
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product or not product.category:
            return False
        return product.category.lower() in [r.lower() for r in restriction_list]
    except (json.JSONDecodeError, TypeError):
        return False


def get_product_restrictions_for_country(db: Session, country_code: str) -> list[str]:
    """Get product restrictions for a country."""
    config = get_country_config(db, country_code)
    if not config or not config.product_restrictions_json:
        return []
    try:
        restrictions = json.loads(config.product_restrictions_json) if isinstance(config.product_restrictions_json, str) else config.product_restrictions_json
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
    """Calculate order totals with country-specific tax and currency."""
    subtotal_decimal = to_decimal(subtotal)
    discount = to_decimal("0")
    
    tax_preview = calculate_tax(subtotal_decimal, country_code, db)
    
    return {
        "country_code": country_code,
        "currency": tax_preview.get("currency", "USD"),
        "tax_type": tax_preview.get("tax_type", "VAT"),
        "tax_name": tax_preview.get("tax_name", "Tax"),
        "tax_rate": float(tax_preview.get("tax_rate", 0)),
        "tax_amount": float(tax_preview.get("tax_amount", 0)),
        "vat_amount": float(tax_preview.get("vat_amount", 0)),
        "net_amount": float(tax_preview.get("net_amount", 0)),
        "total_amount": float(tax_preview.get("total_amount", 0)),
        "is_inclusive": tax_preview.get("is_inclusive", False),
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
    config = get_country_config(db, country_code)
    if not config:
        return {"min_days": 1, "max_days": 7, "holidays": []}
    
    holidays = get_public_holidays_for_country(db, country_code)
    
    return {
        "min_days": 1,
        "max_days": 7,
        "holidays": holidays,
        "logistics_model": config.logistics_model or "basic_delivery",
    }


def get_commission_tiers_for_country(db: Session, country_code: str) -> list[dict[str, Any]]:
    """Get commission tiers for a country."""
    config = get_country_config(db, country_code)
    if not config or not config.commission_tiers_json:
        return []
    try:
        tiers = json.loads(config.commission_tiers_json) if isinstance(config.commission_tiers_json, str) else config.commission_tiers_json
        return tiers or []
    except (json.JSONDecodeError, TypeError):
        return []


def get_supplier_requirements_for_country(db: Session, country_code: str) -> dict[str, Any]:
    """Get supplier requirements for a country."""
    config = get_country_config(db, country_code)
    if not config or not config.supplier_requirements_json:
        return {"kyc_level": "standard", "required_documents": [], "approval_required": True}
    try:
        reqs = json.loads(config.supplier_requirements_json) if isinstance(config.supplier_requirements_json, str) else config.supplier_requirements_json
        return reqs or {}
    except (json.JSONDecodeError, TypeError):
        return {"kyc_level": "standard", "required_documents": [], "approval_required": True}


def get_payout_settings_for_country(db: Session, country_code: str) -> dict[str, Any]:
    """Get payout settings for a country."""
    config = get_country_config(db, country_code)
    if not config or not config.payout_settings_json:
        return {"minimum_payout_amount": 100.0, "payout_schedule": "weekly", "payout_day": "sunday"}
    try:
        settings = json.loads(config.payout_settings_json) if isinstance(config.payout_settings_json, str) else config.payout_settings_json
        return settings or {}
    except (json.JSONDecodeError, TypeError):
        return {"minimum_payout_amount": 100.0, "payout_schedule": "weekly", "payout_day": "sunday"}
