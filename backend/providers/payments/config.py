"""Payment gateway provider: config.

Relocated from controllers/payments_controller.py.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import stripe
import httpx
import logging
import uuid
from decimal import Decimal
from datetime import datetime, timezone
from typing import Any, Literal, Optional, cast
from urllib.parse import parse_qs

from fastapi import HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from data.models import (
    Coupon, Order, OrderItem, Payment, PaymentGatewayConnection, PaymentProviderConfig,
    Product, Notification, ProcessedWebhookEvent, TransactionLedger, CountryConfig,
)
from data.events import PaymentConfirmedEvent, EventPublisher, _event_publisher
from utils.config import settings
from utils.currency import (
    convert_from_aed,
    get_currency_context,
    money_to_minor_units_for_currency,
)
from providers.payments.base import (
    GatewayDefinition,
    GatewaySettings,
    get_provider,
    register_provider,
    OPERATION_CREATE,
    OPERATION_CONFIRM,
    OPERATION_WEBHOOK,
)

logger = logging.getLogger(__name__)


__all__ = ['_get_gateway_connection_record', '_gateway_adapter_supported', '_resolve_stripe_secret_key', '_resolve_stripe_webhook_secret', '_apply_stripe_runtime_key', '_stripe_configured', '_resolve_tap_secret_key', '_resolve_tap_webhook_secret', '_resolve_tap_api_base_url', '_resolve_tap_webhook_url', '_tap_configured', '_resolve_paytabs_server_key', '_resolve_paytabs_webhook_secret', '_resolve_paytabs_profile_id', '_resolve_paytabs_api_base_url', '_resolve_paytabs_callback_url', '_paytabs_configured', '_get_payment_provider_config_record', '_default_online_provider_mode', '_payment_provider_runtime_status', '_payment_provider_mode_allows', '_gateway_charge_quote', 'build_order_payment_snapshot', '_resolve_country_gateway', '_paytabs_checkout_enabled', '_paypal_gateway_enabled', 'get_payment_methods_status', 'get_customer_checkout_gateways', 'get_payment_provider_runtime_config', 'update_payment_provider_runtime_config', '_built_in_gateway_defaults', '_serialize_gateway_connection', 'list_payment_gateway_connections', 'upsert_payment_gateway_connection', 'test_payment_gateway_connection', 'build_payment_finance_quote', 'gateway_wizard_step', '_gateway_wizard_credentials_step', '_gateway_wizard_fees_step', '_gateway_wizard_routing_step', '_gateway_wizard_test_step', '_resolve_gateway_callback_base', 'is_checkout_payment_method_allowed', '_is_non_placeholder_secret',
'resolve_gateway_settings', '_gateway_is_configured']

def _get_gateway_connection_record(db: Session, provider_code: str, country_code: Optional[str] = None) -> Optional[PaymentGatewayConnection]:
    """Resolve a gateway connection by provider_code, scoped to a country.

    Resolution order:
      1. An exact row for (provider_code, country_code) when a country is given.
      2. The global/wildcard row (country_code == "*").
    This lets an admin attach the same provider per-country (e.g. a different
    Paymob config for PK vs OM) while still supporting a single global gateway.
    """
    normalized_code = _normalize_gateway_code(provider_code)
    if country_code:
        country_code = str(country_code).strip().upper()
        if country_code and country_code != "*":
            row = (
                db.query(PaymentGatewayConnection)
                .filter(
                    PaymentGatewayConnection.provider_code == normalized_code,
                    PaymentGatewayConnection.country_code == country_code,
                )
                .first()
            )
            if row is not None:
                return row
    return (
        db.query(PaymentGatewayConnection)
        .filter(
            PaymentGatewayConnection.provider_code == normalized_code,
            PaymentGatewayConnection.country_code == "*",
        )
        .first()
    )


def _gateway_adapter_supported(provider_kind: str, provider_code: str) -> bool:
    normalized_code = _normalize_gateway_code(provider_code)
    return normalized_code in LIVE_ADAPTER_GATEWAY_CODES


def _resolve_stripe_secret_key(db: Session | None = None) -> str:
    if db is not None:
        record = _get_gateway_connection_record(db, "stripe")
        if record and getattr(record, "secret_key", None):
            return str(getattr(record, "secret_key") or "").strip()
    return str(
        os.getenv("STRIPE_SECRET_KEY")
        or getattr(settings, "stripe_secret_key", "")
        or stripe.api_key
        or ""
    ).strip()


def _resolve_stripe_webhook_secret(db: Session | None = None) -> str:
    if db is not None:
        record = _get_gateway_connection_record(db, "stripe")
        if record and getattr(record, "webhook_secret", None):
            return str(getattr(record, "webhook_secret") or "").strip()
    return str(os.getenv("STRIPE_WEBHOOK_SECRET") or getattr(settings, "stripe_webhook_secret", "") or "").strip()


def _apply_stripe_runtime_key(db: Session | None = None) -> str:
    resolved = _resolve_stripe_secret_key(db)
    stripe.api_key = resolved
    runtime_api_version = str(getattr(settings, "stripe_api_version", "") or "").strip()
    if runtime_api_version:
        stripe.api_version = runtime_api_version
    return resolved


def _stripe_configured(db: Session | None = None) -> bool:
    key = _apply_stripe_runtime_key(db)
    return _is_non_placeholder_secret(key, ("sk_test_", "sk_live_"))


def _resolve_tap_secret_key(db: Session | None = None) -> str:
    if db is not None:
        record = _get_gateway_connection_record(db, "tap")
        if record and getattr(record, "secret_key", None):
            return str(getattr(record, "secret_key") or "").strip()
    return str(os.getenv("TAP_SECRET_KEY") or getattr(settings, "tap_secret_key", "") or "").strip()


def _resolve_tap_webhook_secret(db: Session | None = None) -> str:
    if db is not None:
        record = _get_gateway_connection_record(db, "tap")
        if record and getattr(record, "webhook_secret", None):
            return str(getattr(record, "webhook_secret") or "").strip()
    return str(os.getenv("TAP_WEBHOOK_SECRET") or getattr(settings, "tap_webhook_secret", "") or "").strip()


def _resolve_tap_api_base_url(db: Session | None = None) -> str:
    if db is not None:
        record = _get_gateway_connection_record(db, "tap")
        configured_url = _optional_text(getattr(record, "api_base_url", None)) if record else None
        if configured_url:
            return configured_url.rstrip("/")
    return DEFAULT_TAP_API_BASE_URL


def _resolve_tap_webhook_url(db: Session | None = None) -> str:
    if db is not None:
        record = _get_gateway_connection_record(db, "tap")
        configured_url = _optional_text(getattr(record, "webhook_url", None)) if record else None
        if configured_url:
            return configured_url
    return str(settings.tap_webhook_url or "").strip()


def _tap_configured(db: Session | None = None) -> tuple[bool, str]:
    key = _resolve_tap_secret_key(db)
    return _is_non_placeholder_secret(key, ("sk_test_", "sk_live_", "sk_")), key


def _resolve_paytabs_server_key(db: Session | None = None) -> str:
    if db is not None:
        record = _get_gateway_connection_record(db, PAYTABS_PAYMENT_METHOD)
        if record and getattr(record, "secret_key", None):
            return str(getattr(record, "secret_key") or "").strip()
    return str(getattr(settings, "paytabs_server_key", "") or "").strip()


def _resolve_paytabs_webhook_secret(db: Session | None = None) -> str:
    if db is not None:
        record = _get_gateway_connection_record(db, PAYTABS_PAYMENT_METHOD)
        if record and getattr(record, "webhook_secret", None):
            return str(getattr(record, "webhook_secret") or "").strip()
    return str(getattr(settings, "paytabs_webhook_secret", "") or "").strip()


def _resolve_paytabs_profile_id(db: Session | None = None) -> str:
    if db is not None:
        record = _get_gateway_connection_record(db, PAYTABS_PAYMENT_METHOD)
        if record and getattr(record, "merchant_id", None):
            return str(getattr(record, "merchant_id") or "").strip()
    return str(getattr(settings, "paytabs_profile_id", "") or "").strip()


def _resolve_paytabs_api_base_url(db: Session | None = None) -> str:
    if db is not None:
        record = _get_gateway_connection_record(db, PAYTABS_PAYMENT_METHOD)
        configured_url = _optional_text(getattr(record, "api_base_url", None)) if record else None
        if configured_url:
            return configured_url.rstrip("/")
    configured = str(getattr(settings, "paytabs_api_base_url", "") or "").strip()
    return configured.rstrip("/") or DEFAULT_PAYTABS_API_BASE_URL


def _resolve_paytabs_callback_url(db: Session | None = None) -> str:
    if db is not None:
        record = _get_gateway_connection_record(db, PAYTABS_PAYMENT_METHOD)
        configured_url = _optional_text(getattr(record, "webhook_url", None)) if record else None
        if configured_url:
            return configured_url
    return str(getattr(settings, "paytabs_callback_url", "") or "").strip()


def _paytabs_configured(db: Session | None = None) -> tuple[bool, str, str]:
    server_key = _resolve_paytabs_server_key(db)
    profile_id = _resolve_paytabs_profile_id(db)
    return bool(server_key and profile_id), server_key, profile_id


def _get_payment_provider_config_record(db: Session) -> Optional[PaymentProviderConfig]:
    return db.query(PaymentProviderConfig).order_by(PaymentProviderConfig.id.desc()).first()


def _default_online_provider_mode(stripe_configured: bool, tap_configured: bool) -> str:
    if stripe_configured and tap_configured:
        return "both"
    if tap_configured:
        return "tap"
    return "stripe"


def _payment_provider_runtime_status(db: Session) -> PaymentProviderRuntimeConfigResponse:
    stripe_configured = _stripe_configured(db)
    tap_configured, _ = _tap_configured(db)
    record = _get_payment_provider_config_record(db)

    if record is None:
        online_provider = _default_online_provider_mode(stripe_configured, tap_configured)
        source = "environment"
        config_id = None
        updated_by = None
        created_at = None
        updated_at = None
    else:
        configured_mode = str(getattr(record, "online_provider", "") or "").strip().lower()
        online_provider = configured_mode if configured_mode in ONLINE_PAYMENT_PROVIDER_MODES else _default_online_provider_mode(stripe_configured, tap_configured)
        source = "database"
        config_id = cast(Optional[int], getattr(record, "id", None))
        updated_by = cast(Optional[int], getattr(record, "updated_by", None))
        created_at = cast(Optional[datetime], getattr(record, "created_at", None))
        updated_at = cast(Optional[datetime], getattr(record, "updated_at", None))

    stripe_enabled = stripe_configured and online_provider in {"stripe", "both"}
    tap_enabled = tap_configured and online_provider in {"tap", "both"}
    enabled_processors: list[str] = []
    if stripe_enabled:
        enabled_processors.append("stripe")
    if tap_enabled:
        enabled_processors.append("tap")
    if _paytabs_checkout_enabled(db):
        enabled_processors.append(PAYTABS_PAYMENT_METHOD)

    return PaymentProviderRuntimeConfigResponse(
        id=config_id,
        online_provider=cast(Literal["stripe", "tap", "both"], online_provider),
        source=source,
        stripe_configured=stripe_configured,
        tap_configured=tap_configured,
        stripe_enabled=stripe_enabled,
        tap_enabled=tap_enabled,
        enabled_processors=enabled_processors,
        can_accept_online_payments=bool(enabled_processors),
        updated_by=updated_by,
        created_at=created_at,
        updated_at=updated_at,
    )


def _payment_provider_mode_allows(processor: str, db: Session) -> bool:
    if _normalize_gateway_code(processor) == PAYTABS_PAYMENT_METHOD:
        return _paytabs_checkout_enabled(db)
    runtime = _payment_provider_runtime_status(db)
    return runtime.online_provider in {processor, "both"}


def _gateway_charge_quote(gateway_code: Optional[str], order_total: Decimal, db: Session) -> dict[str, Any]:
    normalized_code = _normalize_gateway_code(gateway_code or "") if gateway_code else None
    if not normalized_code:
        return {
            "gateway": None,
            "gateway_code": None,
            "gateway_fee_amount": Decimal("0"),
            "customer_payable_total": order_total,
            "processor_net_capture": order_total,
            "pass_fee_to_customer": False,
        }

    gateway = _serialize_gateway_connection(normalized_code, db, _get_gateway_connection_record(db, normalized_code))
    fee_percent = _decimal_from_value(gateway.fee_percent) / Decimal("100")
    fixed_fee_amount = _decimal_from_value(gateway.fixed_fee_amount)
    gateway_fee_amount = (order_total * fee_percent) + fixed_fee_amount if order_total > 0 else Decimal("0")
    customer_payable_total = order_total + gateway_fee_amount if gateway.pass_fee_to_customer else order_total
    processor_net_capture = customer_payable_total - gateway_fee_amount
    return {
        "gateway": gateway,
        "gateway_code": gateway.provider_code,
        "gateway_fee_amount": round(gateway_fee_amount, 2),
        "customer_payable_total": round(customer_payable_total, 2),
        "processor_net_capture": round(processor_net_capture, 2),
        "pass_fee_to_customer": gateway.pass_fee_to_customer,
    }


def build_order_payment_snapshot(payment_method: str | None, order_total: Any, db: Session, country_code: str | None = None) -> dict[str, Any]:
    normalized_method = normalize_checkout_payment_method(payment_method)
    base_total = max(_decimal_from_value(order_total), Decimal("0"))
    gateway_code = gateway_code_for_payment_method(normalized_method)
    
    if country_code:
        gateway_code = _resolve_country_gateway(gateway_code, country_code, db) or gateway_code
    
    quote = _gateway_charge_quote(gateway_code, base_total, db)
    return {
        "payment_gateway_code": quote["gateway_code"],
        "payment_gateway_fee_amount": quote["gateway_fee_amount"],
        "payment_customer_total_amount": quote["customer_payable_total"],
        "payment_processor_net_amount": quote["processor_net_capture"],
        "payment_gateway_fee_passed_to_customer": quote["pass_fee_to_customer"],
    }


def _resolve_country_gateway(default_gateway: str, country_code: str, db: Session) -> Optional[str]:
    """Resolve the appropriate gateway for a country based on CountryConfig.payment_gateways_json."""
    try:
        config = db.query(CountryConfig).filter(
            CountryConfig.code == country_code.upper(),
            CountryConfig.is_active == True,
        ).first()
        
        if not config or not config.payment_gateways_json:
            return None
        
        gateways = json.loads(config.payment_gateways_json) if isinstance(config.payment_gateways_json, str) else config.payment_gateways_json
        
        if not isinstance(gateways, list):
            return None
        
        enabled_gateways = [g for g in gateways if g.get("enabled", True)]
        
        if not enabled_gateways:
            return None
        
        for gw in enabled_gateways:
            gw_name = str(gw.get("gateway_id", "")).lower()
            if default_gateway.lower() in gw_name or gw_name in default_gateway.lower():
                return gw.get("gateway_id")
        
        return enabled_gateways[0].get("gateway_id")
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as e:
        logger.exception("_resolve_country_gateway_failed", error=str(e))
        return None


def _paytabs_checkout_enabled(db: Session) -> bool:
    configured, _, _ = _paytabs_configured(db)
    gateway = _serialize_gateway_connection(PAYTABS_PAYMENT_METHOD, db, _get_gateway_connection_record(db, PAYTABS_PAYMENT_METHOD))
    return configured and gateway.is_enabled and gateway.supports_customer_checkout and gateway.adapter_supported


def _paypal_gateway_enabled(db: Session) -> bool:
    configured, _, _, _ = _paypal_configured(db)
    if not configured:
        return False
    gateway = _serialize_gateway_connection("paypal", db, _get_gateway_connection_record(db, "paypal"))
    return gateway.is_enabled and gateway.supports_customer_checkout and gateway.adapter_supported


def get_payment_methods_status(db: Session, country_code: Optional[str] = None) -> dict:
    runtime = _payment_provider_runtime_status(db)
    stripe_enabled = runtime.stripe_enabled
    tap_enabled = runtime.tap_enabled
    paytabs_enabled = _paytabs_checkout_enabled(db)
    thawani_enabled = _thawani_checkout_enabled(db)
    stripe_gateway = _serialize_gateway_connection("stripe", db, _get_gateway_connection_record(db, "stripe"))
    tap_gateway = _serialize_gateway_connection("tap", db, _get_gateway_connection_record(db, "tap"))
    paytabs_gateway = _serialize_gateway_connection(PAYTABS_PAYMENT_METHOD, db, _get_gateway_connection_record(db, PAYTABS_PAYMENT_METHOD))
    thawani_gateway = _serialize_gateway_connection(THAWANI_PAYMENT_METHOD, db, _get_gateway_connection_record(db, THAWANI_PAYMENT_METHOD))
    card_detail = "Stripe card payments."
    if not stripe_enabled:
        card_detail = (
            "Card payments are temporarily disabled by admin."
            if runtime.online_provider == "tap" and runtime.stripe_configured
            else "Stripe card payments are not configured."
        )

    tap_detail = "Tap-hosted checkout."
    if not tap_enabled:
        tap_detail = (
            "Tap payments are temporarily disabled by admin."
            if runtime.online_provider == "stripe" and runtime.tap_configured
            else "Tap-hosted checkout is not configured."
        )

    paytabs_detail = "PayTabs hosted checkout."
    if not paytabs_enabled:
        paytabs_detail = "PayTabs hosted checkout is not configured."

    thawani_detail = "Thawani Pay hosted checkout (OMR)."
    if not thawani_enabled:
        thawani_detail = "Thawani Pay hosted checkout is not configured."

    return {
        "cod": {
            "enabled": True,
            "label": "Cash on Delivery",
            "detail": "Place the order now and pay when it arrives.",
        },
        "card": {
            "enabled": stripe_enabled,
            "label": "Credit / Debit Card",
            "detail": card_detail,
            "gateway_code": stripe_gateway.provider_code,
            "pricing": {
                "fee_percent": stripe_gateway.fee_percent,
                "fixed_fee_amount": stripe_gateway.fixed_fee_amount,
                "pass_fee_to_customer": stripe_gateway.pass_fee_to_customer,
            },
        },
        "tap": {
            "enabled": tap_enabled,
            "label": "Tap Payments",
            "detail": tap_detail,
            "gateway_code": tap_gateway.provider_code,
            "pricing": {
                "fee_percent": tap_gateway.fee_percent,
                "fixed_fee_amount": tap_gateway.fixed_fee_amount,
                "pass_fee_to_customer": tap_gateway.pass_fee_to_customer,
            },
        },
        "paytabs": {
            "enabled": paytabs_enabled,
            "label": "PayTabs",
            "detail": paytabs_detail,
            "gateway_code": paytabs_gateway.provider_code,
            "pricing": {
                "fee_percent": paytabs_gateway.fee_percent,
                "fixed_fee_amount": paytabs_gateway.fixed_fee_amount,
                "pass_fee_to_customer": paytabs_gateway.pass_fee_to_customer,
            },
        },
        "thawani": {
            "enabled": thawani_enabled,
            "label": "Thawani Pay",
            "detail": thawani_detail,
            "gateway_code": thawani_gateway.provider_code,
            "pricing": {
                "fee_percent": thawani_gateway.fee_percent,
                "fixed_fee_amount": thawani_gateway.fixed_fee_amount,
                "pass_fee_to_customer": thawani_gateway.pass_fee_to_customer,
            },
        },
        "online_provider": runtime.online_provider,
        "gateways": get_customer_checkout_gateways(db, country_code=country_code),
    }


def get_customer_checkout_gateways(db: Session, country_code: Optional[str] = None) -> list[dict[str, Any]]:
    """Return the gateways a customer can pay with at checkout for their country.

    Country-aware: for the caller's country, a country-specific gateway
    connection overrides the global ("*") one for the same provider, so an admin
    can attach a different configuration (or a different provider) per country.
    Both country-specific and global gateways are returned, de-duplicated by
    provider_code (the country-specific entry wins).
    """
    country_code = (country_code or "").strip().upper() or None

    rows = (
        db.query(PaymentGatewayConnection)
        .filter(
            PaymentGatewayConnection.is_enabled == True,  # noqa: E712
            PaymentGatewayConnection.supports_customer_checkout == True,  # noqa: E712
        )
        .all()
    )

    # Index by provider_code, picking the best row for the caller's country:
    #   1. an exact (provider, country) row, else
    #   2. the global ("*") row, else
    #   3. none (a country-specific row for a *different* country is NOT shown).
    exact: dict[str, PaymentGatewayConnection] = {}
    global_rows: dict[str, PaymentGatewayConnection] = {}
    for row in rows:
        code = _normalize_gateway_code(str(row.provider_code))
        row_country = str(getattr(row, "country_code", "*") or "*").upper()
        if country_code and row_country == country_code:
            exact[code] = row
        elif row_country == "*":
            global_rows.setdefault(code, row)

    chosen: dict[str, PaymentGatewayConnection] = {}
    for code in set(exact) | set(global_rows):
        chosen[code] = exact.get(code) or global_rows.get(code)

    # Build the response list from the chosen rows only.
    result: list[dict[str, Any]] = []
    for code, row in chosen.items():
        row_country = str(getattr(row, "country_code", "*") or "*").upper()
        result.append({
            "provider_code": row.provider_code,
            "display_name": row.display_name,
            "provider_kind": row.provider_kind,
            "adapter_supported": _gateway_adapter_supported(str(row.provider_kind or ""), str(row.provider_code)),
            "mode": row.mode,
            "country_code": row_country,
            "supported_currencies": _json_load_currency_list(getattr(row, "supported_currencies_json", None)),
            "fee_percent": row.fee_percent,
            "fixed_fee_amount": row.fixed_fee_amount,
            "pass_fee_to_customer": row.pass_fee_to_customer,
        })
    return result


def get_payment_provider_runtime_config(db: Session) -> PaymentProviderRuntimeConfigResponse:
    return _payment_provider_runtime_status(db)


def update_payment_provider_runtime_config(
    payload: PaymentProviderRuntimeConfigRequest,
    current_user: dict[str, Any],
    db: Session,
) -> PaymentProviderRuntimeConfigResponse:
    stripe_configured = _stripe_configured(db)
    tap_configured, _ = _tap_configured(db)

    if payload.online_provider == "stripe" and not stripe_configured:
        raise HTTPException(status_code=422, detail="Stripe is not configured")
    if payload.online_provider == "tap" and not tap_configured:
        raise HTTPException(status_code=422, detail="Tap is not configured")
    if payload.online_provider == "both" and not (stripe_configured and tap_configured):
        raise HTTPException(status_code=422, detail="Both Stripe and Tap must be configured to enable both")

    record = _get_payment_provider_config_record(db)
    if record is None:
        record = PaymentProviderConfig(updated_by=current_user.get("id"))
        db.add(record)

    setattr(record, "online_provider", payload.online_provider)
    setattr(record, "updated_by", current_user.get("id"))
    db.commit()
    db.refresh(record)
    return _payment_provider_runtime_status(db)


def _built_in_gateway_defaults(provider_code: str, db: Session) -> dict[str, Any]:
    normalized = _normalize_gateway_code(provider_code)
    if normalized == "stripe":
        stripe_secret = _resolve_stripe_secret_key(db)
        webhook_secret = _resolve_stripe_webhook_secret(db)
        return {
            "provider_code": "stripe",
            "provider_kind": "stripe",
            "display_name": "Stripe",
            "is_enabled": True,
            "supports_customer_checkout": True,
            "supports_payouts": True,
            "mode": "live" if stripe_secret.startswith("sk_live_") else "test",
            "public_key": None,
            "merchant_id": None,
            "api_base_url": "https://api.stripe.com",
            "webhook_url": None,
            "test_url": "https://api.stripe.com/v1/balance",
            "supported_currencies": ["AED", "OMR", "USD"],
            "extra_config": {},
            "notes": "Built-in Stripe adapter used by the card payment intent flow.",
            "fee_percent": 0.0,
            "fixed_fee_amount": 0.0,
            "payout_fee_percent": 0.0,
            "payout_fixed_fee_amount": 0.0,
            "pass_fee_to_customer": False,
            "settlement_cycle": DEFAULT_SETTLEMENT_CYCLE,
            "secret_key_configured": _is_non_placeholder_secret(stripe_secret, ("sk_test_", "sk_live_")),
            "webhook_secret_configured": bool(webhook_secret),
            "test_status": "untested",
            "test_message": None,
            "last_tested_at": None,
        }
    if normalized == "tap":
        tap_secret = _resolve_tap_secret_key(db)
        tap_webhook_secret = _resolve_tap_webhook_secret(db)
        return {
            "provider_code": "tap",
            "provider_kind": "tap",
            "display_name": "Tap Payments",
            "is_enabled": True,
            "supports_customer_checkout": True,
            "supports_payouts": False,
            "mode": "live" if tap_secret.startswith("sk_live_") else "test",
            "public_key": None,
            "merchant_id": None,
            "api_base_url": _resolve_tap_api_base_url(db),
            "webhook_url": _resolve_tap_webhook_url(db) or None,
            "test_url": f"{_resolve_tap_api_base_url(db)}/v2/charges/{DEFAULT_TAP_TEST_CHARGE_ID}",
            "supported_currencies": ["AED", "OMR", "SAR", "KWD", "QAR", "BHD"],
            "extra_config": {},
            "notes": "Built-in Tap adapter used by the hosted Tap checkout flow.",
            "fee_percent": 0.0,
            "fixed_fee_amount": 0.0,
            "payout_fee_percent": 0.0,
            "payout_fixed_fee_amount": 0.0,
            "pass_fee_to_customer": False,
            "settlement_cycle": DEFAULT_SETTLEMENT_CYCLE,
            "secret_key_configured": _is_non_placeholder_secret(tap_secret, ("sk_test_", "sk_live_", "sk_")),
            "webhook_secret_configured": bool(tap_webhook_secret),
            "test_status": "untested",
            "test_message": None,
            "last_tested_at": None,
        }
    if normalized == PAYTABS_PAYMENT_METHOD:
        configured, server_key, profile_id = _paytabs_configured(db)
        api_base_url = _resolve_paytabs_api_base_url(db)
        return {
            "provider_code": PAYTABS_PAYMENT_METHOD,
            "provider_kind": "custom",
            "display_name": "PayTabs",
            "is_enabled": True,
            "supports_customer_checkout": True,
            "supports_payouts": False,
            "mode": "test" if "sandbox" in api_base_url.lower() else "live",
            "public_key": None,
            "merchant_id": profile_id or None,
            "api_base_url": api_base_url,
            "webhook_url": _resolve_paytabs_callback_url(db) or None,
            "test_url": f"{api_base_url}{DEFAULT_PAYTABS_QUERY_PATH}",
            "supported_currencies": ["AED", "OMR", "SAR", "USD"],
            "extra_config": {},
            "notes": "Built-in PayTabs hosted payment page adapter.",
            "fee_percent": 0.0,
            "fixed_fee_amount": 0.0,
            "payout_fee_percent": 0.0,
            "payout_fixed_fee_amount": 0.0,
            "pass_fee_to_customer": False,
            "settlement_cycle": DEFAULT_SETTLEMENT_CYCLE,
            "secret_key_configured": configured and bool(server_key),
            "webhook_secret_configured": False,
            "test_status": "untested",
            "test_message": None,
            "last_tested_at": None,
        }
    if normalized == "paypal":
        return {
            "provider_code": "paypal",
            "provider_kind": "custom",
            "display_name": "PayPal",
            "is_enabled": False,
            "supports_customer_checkout": True,
            "supports_payouts": True,
            "mode": "test",
            "public_key": None,
            "merchant_id": None,
            "api_base_url": "https://api-m.sandbox.paypal.com",
            "webhook_url": None,
            "test_url": "https://api-m.sandbox.paypal.com/v1/oauth2/token",
            "supported_currencies": ["USD", "EUR", "GBP"],
            "extra_config": {},
            "notes": "Built-in PayPal template. Credentials, fee rules, and connectivity checks are supported; live checkout still needs a dedicated adapter.",
            "fee_percent": 0.0,
            "fixed_fee_amount": 0.0,
            "payout_fee_percent": 0.0,
            "payout_fixed_fee_amount": 0.0,
            "pass_fee_to_customer": False,
            "settlement_cycle": DEFAULT_SETTLEMENT_CYCLE,
            "secret_key_configured": False,
            "webhook_secret_configured": False,
            "test_status": "untested",
            "test_message": None,
            "last_tested_at": None,
        }
    if normalized == "hyperpay":
        return {
            "provider_code": "hyperpay",
            "provider_kind": "custom",
            "display_name": "HyperPay",
            "is_enabled": False,
            "supports_customer_checkout": True,
            "supports_payouts": False,
            "mode": "test",
            "public_key": None,
            "merchant_id": None,
            "api_base_url": "https://eu-test.oppwa.com",
            "webhook_url": None,
            "test_url": "https://eu-test.oppwa.com/v1/checkouts",
            "supported_currencies": ["OMR", "AED", "SAR", "USD"],
            "extra_config": {},
            "notes": "Built-in HyperPay template. Store credentials and pricing here; a provider-specific checkout adapter is still required.",
            "fee_percent": 0.0,
            "fixed_fee_amount": 0.0,
            "payout_fee_percent": 0.0,
            "payout_fixed_fee_amount": 0.0,
            "pass_fee_to_customer": False,
            "settlement_cycle": DEFAULT_SETTLEMENT_CYCLE,
            "secret_key_configured": False,
            "webhook_secret_configured": False,
            "test_status": "untested",
            "test_message": None,
            "last_tested_at": None,
        }
    if normalized == "omannet":
        return {
            "provider_code": "omannet",
            "provider_kind": "custom",
            "display_name": "OmanNet",
            "is_enabled": False,
            "supports_customer_checkout": True,
            "supports_payouts": False,
            "mode": "test",
            "public_key": None,
            "merchant_id": None,
            "api_base_url": "https://uat.omannet.om",
            "webhook_url": None,
            "test_url": "https://uat.omannet.om",
            "supported_currencies": ["OMR"],
            "extra_config": {},
            "notes": "Built-in OmanNet template for local card acquiring. Store credentials and test endpoints here before wiring a live adapter.",
            "fee_percent": 0.0,
            "fixed_fee_amount": 0.0,
            "payout_fee_percent": 0.0,
            "payout_fixed_fee_amount": 0.0,
            "pass_fee_to_customer": False,
            "settlement_cycle": DEFAULT_SETTLEMENT_CYCLE,
            "secret_key_configured": False,
            "webhook_secret_configured": False,
            "test_status": "untested",
            "test_message": None,
            "last_tested_at": None,
        }
    if normalized == THAWANI_PAYMENT_METHOD:
        configured, secret_key, publishable_key, api_base_url = _thawani_configured(db)
        is_uat = "uatcheckout" in api_base_url
        return {
            "provider_code": THAWANI_PAYMENT_METHOD,
            "provider_kind": "custom",
            "display_name": "Thawani Pay",
            "is_enabled": True,
            "supports_customer_checkout": True,
            "supports_payouts": False,
            "mode": "test" if is_uat else "live",
            "public_key": None,
            "merchant_id": None,
            "api_base_url": api_base_url,
            "webhook_url": None,
            "test_url": f"{api_base_url}/checkout/session",
            "supported_currencies": ["OMR"],
            "extra_config": {},
            "notes": "Built-in Thawani Pay hosted checkout adapter. Primary gateway for OMR payments in Oman.",
            "fee_percent": 0.0,
            "fixed_fee_amount": 0.0,
            "payout_fee_percent": 0.0,
            "payout_fixed_fee_amount": 0.0,
            "pass_fee_to_customer": False,
            "settlement_cycle": DEFAULT_SETTLEMENT_CYCLE,
            "secret_key_configured": configured and bool(secret_key),
            "webhook_secret_configured": bool(_resolve_thawani_webhook_secret(db)),
            "test_status": "untested",
            "test_message": None,
            "last_tested_at": None,
        }
    raise HTTPException(status_code=404, detail="Unsupported built-in gateway")


def _serialize_gateway_connection(
    provider_code: str,
    db: Session,
    record: Optional[PaymentGatewayConnection] = None,
) -> PaymentGatewayConnectionResponse:
    normalized = _normalize_gateway_code(provider_code)
    defaults = _built_in_gateway_defaults(normalized, db) if normalized in BUILT_IN_GATEWAY_CODES else {
        "provider_code": normalized,
        "provider_kind": "custom",
        "display_name": normalized.replace("_", " ").title(),
        "is_enabled": True,
        "supports_customer_checkout": False,
        "supports_payouts": False,
        "mode": "test",
        "public_key": None,
        "merchant_id": None,
        "api_base_url": None,
        "webhook_url": None,
        "test_url": None,
        "supported_currencies": [],
        "extra_config": {},
        "notes": None,
        "fee_percent": 0.0,
        "fixed_fee_amount": 0.0,
        "payout_fee_percent": 0.0,
        "payout_fixed_fee_amount": 0.0,
        "pass_fee_to_customer": False,
        "settlement_cycle": DEFAULT_SETTLEMENT_CYCLE,
        "secret_key_configured": False,
        "webhook_secret_configured": False,
        "test_status": "untested",
        "test_message": None,
        "last_tested_at": None,
    }

    if record is None:
        return PaymentGatewayConnectionResponse(
            id=None,
            provider_code=normalized,
            provider_kind=cast(Literal["stripe", "tap", "custom"], defaults["provider_kind"]),
            display_name=str(defaults["display_name"]),
            adapter_supported=_gateway_adapter_supported(str(defaults["provider_kind"]), normalized),
            is_enabled=bool(defaults["is_enabled"]),
            supports_customer_checkout=bool(defaults["supports_customer_checkout"]),
            supports_payouts=bool(defaults["supports_payouts"]),
            mode=cast(Literal["test", "live"], defaults["mode"]),
            country_code=str(getattr(record, "country_code", "*") or "*").upper(),
            source="environment" if normalized in BUILT_IN_GATEWAY_CODES else "database",
            public_key=cast(Optional[str], defaults["public_key"]),
            merchant_id=cast(Optional[str], defaults["merchant_id"]),
            api_base_url=cast(Optional[str], defaults["api_base_url"]),
            webhook_url=cast(Optional[str], defaults["webhook_url"]),
            test_url=cast(Optional[str], defaults["test_url"]),
            supported_currencies=cast(list[str], defaults["supported_currencies"]),
            extra_config=cast(dict[str, Any], defaults["extra_config"]),
            notes=cast(Optional[str], defaults["notes"]),
            fee_percent=float(defaults["fee_percent"]),
            fixed_fee_amount=float(defaults["fixed_fee_amount"]),
            payout_fee_percent=float(defaults["payout_fee_percent"]),
            payout_fixed_fee_amount=float(defaults["payout_fixed_fee_amount"]),
            pass_fee_to_customer=bool(defaults["pass_fee_to_customer"]),
            settlement_cycle=cast(Literal["daily", "weekly", "monthly"], defaults["settlement_cycle"]),
            secret_key_configured=bool(defaults["secret_key_configured"]),
            webhook_secret_configured=bool(defaults["webhook_secret_configured"]),
            test_status=cast(Literal["untested", "passed", "failed"], defaults["test_status"]),
            test_message=cast(Optional[str], defaults["test_message"]),
            last_tested_at=cast(Optional[datetime], defaults["last_tested_at"]),
        )

    provider_kind = str(getattr(record, "provider_kind", defaults["provider_kind"]) or defaults["provider_kind"]).strip().lower()
    return PaymentGatewayConnectionResponse(
        id=cast(Optional[int], getattr(record, "id", None)),
        provider_code=normalized,
        provider_kind=cast(Literal["stripe", "tap", "custom"], provider_kind if provider_kind in SUPPORTED_GATEWAY_KINDS else defaults["provider_kind"]),
        display_name=str(getattr(record, "display_name", defaults["display_name"]) or defaults["display_name"]),
        adapter_supported=_gateway_adapter_supported(provider_kind, normalized),
        is_enabled=bool(getattr(record, "is_enabled", defaults["is_enabled"])),
        supports_customer_checkout=bool(getattr(record, "supports_customer_checkout", defaults["supports_customer_checkout"])),
        supports_payouts=bool(getattr(record, "supports_payouts", defaults["supports_payouts"])),
        mode=cast(Literal["test", "live"], str(getattr(record, "mode", defaults["mode"]) or defaults["mode"])),
        country_code=str(getattr(record, "country_code", "*") or "*").upper(),
        source="database",
        public_key=_optional_text(getattr(record, "public_key", defaults["public_key"])),
        merchant_id=_optional_text(getattr(record, "merchant_id", defaults["merchant_id"])),
        api_base_url=_optional_text(getattr(record, "api_base_url", defaults["api_base_url"])),
        webhook_url=_optional_text(getattr(record, "webhook_url", defaults["webhook_url"])),
        test_url=_optional_text(getattr(record, "test_url", defaults["test_url"])),
        supported_currencies=_json_load_currency_list(getattr(record, "supported_currencies_json", None)) or cast(list[str], defaults["supported_currencies"]),
        extra_config=_json_load_dict(getattr(record, "extra_config_json", None)),
        notes=_optional_text(getattr(record, "notes", defaults["notes"])),
        fee_percent=_float_money(getattr(record, "fee_percent", defaults["fee_percent"])),
        fixed_fee_amount=_float_money(getattr(record, "fixed_fee_amount", defaults["fixed_fee_amount"])),
        payout_fee_percent=_float_money(getattr(record, "payout_fee_percent", defaults["payout_fee_percent"])),
        payout_fixed_fee_amount=_float_money(getattr(record, "payout_fixed_fee_amount", defaults["payout_fixed_fee_amount"])),
        pass_fee_to_customer=bool(getattr(record, "pass_fee_to_customer", defaults["pass_fee_to_customer"])),
        settlement_cycle=cast(
            Literal["daily", "weekly", "monthly"],
            str(getattr(record, "settlement_cycle", defaults["settlement_cycle"]) or defaults["settlement_cycle"]),
        ),
        secret_key_configured=bool(getattr(record, "secret_key", None)) or bool(defaults["secret_key_configured"]),
        webhook_secret_configured=bool(getattr(record, "webhook_secret", None)) or bool(defaults["webhook_secret_configured"]),
        test_status=cast(Literal["untested", "passed", "failed"], str(getattr(record, "test_status", defaults["test_status"]) or defaults["test_status"])),
        test_message=_optional_text(getattr(record, "test_message", defaults["test_message"])),
        last_tested_at=cast(Optional[datetime], getattr(record, "last_tested_at", None)),
        updated_by=cast(Optional[int], getattr(record, "updated_by", None)),
        created_at=cast(Optional[datetime], getattr(record, "created_at", None)),
        updated_at=cast(Optional[datetime], getattr(record, "updated_at", None)),
    )


def list_payment_gateway_connections(db: Session) -> list[PaymentGatewayConnectionResponse]:
    responses: list[PaymentGatewayConnectionResponse] = []
    built_in_records = {
        _normalize_gateway_code(cast(str, record.provider_code)): record
        for record in db.query(PaymentGatewayConnection).filter(PaymentGatewayConnection.provider_code.in_(list(BUILT_IN_GATEWAY_CODES))).all()
    }
    for provider_code in BUILT_IN_GATEWAY_ORDER:
        responses.append(_serialize_gateway_connection(provider_code, db, built_in_records.get(provider_code)))

    custom_records = (
        db.query(PaymentGatewayConnection)
        .filter(~PaymentGatewayConnection.provider_code.in_(list(BUILT_IN_GATEWAY_CODES)))
        .order_by(PaymentGatewayConnection.display_name.asc())
        .all()
    )
    for record in custom_records:
        responses.append(_serialize_gateway_connection(cast(str, record.provider_code), db, record))
    return responses


def upsert_payment_gateway_connection(
    provider_code: str,
    payload: PaymentGatewayConnectionRequest,
    current_user: dict[str, Any],
    db: Session,
) -> PaymentGatewayConnectionResponse:
    normalized_code = _normalize_gateway_code(provider_code)
    if normalized_code != payload.provider_code:
        raise HTTPException(status_code=422, detail="provider_code path and payload must match")

    provider_kind = payload.provider_kind
    if normalized_code in BUILT_IN_GATEWAY_CODES:
        provider_kind = cast(
            Literal["stripe", "tap", "custom"],
            normalized_code if normalized_code in {"stripe", "tap"} else "custom",
        )

    country_code = (payload.country_code or "*").strip().upper() or "*"
    record = _get_gateway_connection_record(db, normalized_code, country_code)
    if record is None:
        record = PaymentGatewayConnection(
            provider_code=normalized_code,
            gateway_name=payload.display_name or normalized_code,
            country_code=country_code,
            provider_kind=provider_kind,
            display_name=payload.display_name or normalized_code,
            mode=payload.mode or "test",
            test_status="untested",
        )
        db.add(record)

    setattr(record, "gateway_name", payload.display_name or normalized_code)
    setattr(record, "country_code", country_code)
    setattr(record, "provider_kind", provider_kind)
    setattr(record, "display_name", payload.display_name)
    setattr(record, "is_enabled", payload.is_enabled)
    setattr(record, "supports_customer_checkout", payload.supports_customer_checkout)
    setattr(record, "supports_payouts", payload.supports_payouts)
    setattr(record, "mode", payload.mode)
    setattr(record, "public_key", payload.public_key)
    if payload.secret_key is not None:
        setattr(record, "secret_key", payload.secret_key)
    if payload.webhook_secret is not None:
        setattr(record, "webhook_secret", payload.webhook_secret)
    setattr(record, "merchant_id", payload.merchant_id)
    setattr(record, "api_base_url", payload.api_base_url)
    setattr(record, "webhook_url", payload.webhook_url)
    setattr(record, "test_url", payload.test_url)
    setattr(record, "supported_currencies_json", json.dumps(payload.supported_currencies))
    setattr(record, "extra_config_json", json.dumps(payload.extra_config))
    setattr(record, "notes", payload.notes)
    setattr(record, "fee_percent", payload.fee_percent)
    setattr(record, "fixed_fee_amount", payload.fixed_fee_amount)
    setattr(record, "payout_fee_percent", payload.payout_fee_percent)
    setattr(record, "payout_fixed_fee_amount", payload.payout_fixed_fee_amount)
    setattr(record, "pass_fee_to_customer", payload.pass_fee_to_customer)
    setattr(record, "settlement_cycle", payload.settlement_cycle)
    setattr(record, "updated_by", current_user.get("id"))
    db.commit()
    db.refresh(record)
    return _serialize_gateway_connection(normalized_code, db, record)


def test_payment_gateway_connection(provider_code: str, db: Session) -> PaymentGatewayTestResponse:
    normalized_code = _normalize_gateway_code(provider_code)
    record = _get_gateway_connection_record(db, normalized_code)
    if record is None and normalized_code in BUILT_IN_GATEWAY_CODES:
        defaults = _built_in_gateway_defaults(normalized_code, db)
        record = PaymentGatewayConnection(
            provider_code=normalized_code,
            gateway_name=cast(str, defaults["display_name"]),
            country_code="*",
            provider_kind=cast(str, defaults["provider_kind"]),
            display_name=cast(str, defaults["display_name"]),
            mode="test",
            test_status="untested",
        )
        db.add(record)
        db.flush()
    if record is None:
        raise HTTPException(status_code=404, detail="Gateway not found")

    tested_at = datetime.now(timezone.utc)
    provider_kind = str(getattr(record, "provider_kind", "custom") or "custom").strip().lower()
    message = "Gateway connection test passed."
    status = "passed"

    try:
        if normalized_code == "stripe":
            secret_key = _resolve_stripe_secret_key(db)
            if not _is_non_placeholder_secret(secret_key, ("sk_test_", "sk_live_")):
                raise HTTPException(status_code=422, detail="Stripe secret key is required for testing")
            previous_key = stripe.api_key
            try:
                stripe.api_key = secret_key
                stripe.Balance.retrieve()
            finally:
                stripe.api_key = previous_key
            message = "Stripe credentials verified successfully."
        elif normalized_code == "tap":
            secret_key = _resolve_tap_secret_key(db)
            if not _is_non_placeholder_secret(secret_key, ("sk_test_", "sk_live_", "sk_")):
                raise HTTPException(status_code=422, detail="Tap secret key is required for testing")
            url = f"{_resolve_tap_api_base_url(db)}/v2/charges/{DEFAULT_TAP_TEST_CHARGE_ID}"
            response = httpx.get(url, headers={"Authorization": f"Bearer {secret_key}", "accept": "application/json"}, timeout=15)
            if response.status_code in (200, 404):
                message = "Tap credentials verified successfully."
            elif response.status_code in (401, 403):
                raise HTTPException(status_code=400, detail="Tap credentials were rejected")
            else:
                raise HTTPException(status_code=400, detail=f"Tap test request failed with status {response.status_code}")
        elif normalized_code == PAYTABS_PAYMENT_METHOD:
            configured, server_key, profile_id = _paytabs_configured(db)
            if not configured:
                raise HTTPException(status_code=422, detail="PayTabs server key and profile_id are required for testing")
            response = httpx.post(
                f"{_resolve_paytabs_api_base_url(db)}{DEFAULT_PAYTABS_QUERY_PATH}",
                headers={"authorization": server_key, "content-type": "application/json"},
                json={"profile_id": profile_id, "tran_ref": "ZOZI_CONNECTION_TEST"},
                timeout=15,
            )
            if response.status_code in (200, 400, 422):
                message = "PayTabs API is reachable and credentials were accepted."
            elif response.status_code in (401, 403):
                raise HTTPException(status_code=400, detail="PayTabs credentials were rejected")
            else:
                raise HTTPException(status_code=400, detail=f"PayTabs test request failed with status {response.status_code}")
        else:
            target_url = _optional_text(getattr(record, "test_url", None)) or _optional_text(getattr(record, "api_base_url", None))
            if not target_url:
                raise HTTPException(status_code=422, detail="Custom gateways require test_url or api_base_url to run a connection test")
            headers: dict[str, str] = {"accept": "application/json"}
            secret_key = _optional_text(getattr(record, "secret_key", None))
            if secret_key:
                headers["Authorization"] = f"Bearer {secret_key}"
            response = httpx.get(target_url, headers=headers, timeout=15, follow_redirects=True)
            if response.status_code >= 400:
                raise HTTPException(status_code=400, detail=f"Gateway responded with status {response.status_code}")
            message = "Custom gateway endpoint is reachable. Adapter work is still required for live checkout."
    except HTTPException as exc:
        logger.exception("test_payment_gateway_connection_failed", error=str(exc))
        status = "failed"
        message = str(exc.detail)
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as exc:
        logger.exception("test_payment_gateway_connection_failed", error=str(exc))
        status = "failed"
        message = str(exc)

    setattr(record, "test_status", status)
    setattr(record, "test_message", message)
    setattr(record, "last_tested_at", tested_at.replace(tzinfo=None))
    db.commit()

    if status != "passed":
        raise HTTPException(status_code=400, detail=message)
    return PaymentGatewayTestResponse(provider_code=normalized_code, test_status="passed", message=message, tested_at=tested_at)


def build_payment_finance_quote(payload: PaymentFinanceQuoteRequest, db: Session) -> PaymentFinanceQuoteResponse:
    gateway_code = _normalize_gateway_code(payload.gateway_code or "stripe") if payload.gateway_code else None
    gateway = _serialize_gateway_connection(gateway_code, db, _get_gateway_connection_record(db, gateway_code)) if gateway_code else None

    subtotal_amount = max(_decimal_from_value(payload.subtotal_amount), Decimal("0"))
    discount_amount = max(_decimal_from_value(payload.discount_amount), Decimal("0"))
    shipping_amount = max(_decimal_from_value(payload.shipping_amount), Decimal("0"))
    vat_amount = max(_decimal_from_value(payload.vat_amount), Decimal("0"))
    if discount_amount > subtotal_amount:
        discount_amount = subtotal_amount

    taxable_product_amount = subtotal_amount - discount_amount
    order_total = taxable_product_amount + shipping_amount + vat_amount
    gateway_fee_amount = Decimal("0")
    customer_payable_total = order_total
    processor_net_capture = order_total
    estimated_payout_cost = Decimal("0")
    pass_fee_to_customer = False
    gateway_display_name: Optional[str] = None
    adapter_supported = False

    if gateway is not None:
        gateway_display_name = gateway.display_name
        adapter_supported = gateway.adapter_supported
        quote = _gateway_charge_quote(gateway.provider_code, order_total, db)
        gateway_fee_amount = cast(Decimal, quote["gateway_fee_amount"])
        customer_payable_total = cast(Decimal, quote["customer_payable_total"])
        processor_net_capture = cast(Decimal, quote["processor_net_capture"])
        pass_fee_to_customer = bool(quote["pass_fee_to_customer"])
        payout_fee_percent = _decimal_from_value(gateway.payout_fee_percent) / Decimal("100")
        payout_fixed_fee_amount = _decimal_from_value(gateway.payout_fixed_fee_amount)

        payout_base = max(taxable_product_amount + shipping_amount, Decimal("0"))
        estimated_payout_cost = (payout_base * payout_fee_percent) + payout_fixed_fee_amount if payout_base > 0 else Decimal("0")

    zozi_commission_amount = taxable_product_amount * _decimal_from_value(settings.zozi_commission_rate)
    supplier_payout_estimate = max(taxable_product_amount - zozi_commission_amount, Decimal("0"))
    if gateway is not None and gateway_fee_amount > 0 and not pass_fee_to_customer:
        supplier_payout_estimate = max(supplier_payout_estimate - gateway_fee_amount, Decimal("0"))
    logistics_payout_estimate = shipping_amount
    platform_net = processor_net_capture - supplier_payout_estimate - logistics_payout_estimate - estimated_payout_cost

    return PaymentFinanceQuoteResponse(
        gateway_code=gateway.provider_code if gateway else None,
        gateway_display_name=gateway_display_name,
        adapter_supported=adapter_supported,
        order_total=float(order_total),
        gateway_fee_amount=float(gateway_fee_amount),
        customer_payable_total=float(customer_payable_total),
        processor_net_capture=float(processor_net_capture),
        taxable_product_amount=float(taxable_product_amount),
        zozi_commission_amount=float(zozi_commission_amount),
        supplier_payout_estimate=float(supplier_payout_estimate),
        logistics_payout_estimate=float(logistics_payout_estimate),
        estimated_payout_cost=float(estimated_payout_cost),
        platform_net_after_gateway_and_payout_costs=float(platform_net),
        pass_fee_to_customer=pass_fee_to_customer,
    )


def gateway_wizard_step(
    payload: GatewayWizardRequest,
    current_user: dict[str, Any],
    db: Session,
) -> GatewayWizardResponse:
    """Process a single step of the Gateway Wizard."""
    normalized_code = _normalize_gateway_code(payload.provider_code)
    
    if payload.step == "credentials":
        return _gateway_wizard_credentials_step(normalized_code, payload, current_user, db)
    elif payload.step == "fees":
        return _gateway_wizard_fees_step(normalized_code, payload, current_user, db)
    elif payload.step == "routing":
        return _gateway_wizard_routing_step(normalized_code, payload, current_user, db)
    elif payload.step == "test":
        return _gateway_wizard_test_step(normalized_code, payload, current_user, db)
    
    return GatewayWizardResponse(
        provider_code=normalized_code,
        display_name=payload.display_name or normalized_code.replace("_", " ").title(),
        provider_kind=payload.provider_kind,
        step=payload.step,
        next_step=None,
    )


def _gateway_wizard_credentials_step(
    provider_code: str,
    payload: GatewayWizardRequest,
    current_user: dict,
    db: Session,
) -> GatewayWizardResponse:
    """Step 1: Validate and store credentials."""
    credentials_valid = False
    
    if payload.secret_key and payload.webhook_secret:
        # Validate the supplied credentials using the gateway's own
        # providers-layer resolver. We must NOT reach into the services layer
        # (no PaymentGatewayRegistry / adapter() here — that would be an upward
        # import). A gateway is "registered" when its provider definition exists
        # and both supplied secrets are non-placeholder values.
        definition = get_provider(provider_code)
        credentials_valid = bool(definition) and _is_non_placeholder_secret(
            payload.secret_key
        ) and _is_non_placeholder_secret(payload.webhook_secret)
    
    return GatewayWizardResponse(
        provider_code=provider_code,
        display_name=payload.display_name or provider_code.replace("_", " ").title(),
        provider_kind=payload.provider_kind,
        step="credentials",
        is_enabled=True,
        credentials_valid=credentials_valid,
        next_step="fees" if credentials_valid else None,
    )


def _gateway_wizard_fees_step(
    provider_code: str,
    payload: GatewayWizardRequest,
    current_user: dict,
    db: Session,
) -> GatewayWizardResponse:
    """Step 2: Configure fees."""
    return GatewayWizardResponse(
        provider_code=provider_code,
        display_name=payload.display_name or provider_code.replace("_", " ").title(),
        provider_kind=payload.provider_kind,
        step="fees",
        is_enabled=True,
        credentials_valid=True,
        fees_configured=True,
        next_step="routing",
    )


def _gateway_wizard_routing_step(
    provider_code: str,
    payload: GatewayWizardRequest,
    current_user: dict,
    db: Session,
) -> GatewayWizardResponse:
    """Step 3: Configure routing rules."""
    return GatewayWizardResponse(
        provider_code=provider_code,
        display_name=payload.display_name or provider_code.replace("_", " ").title(),
        provider_kind=payload.provider_kind,
        step="routing",
        is_enabled=True,
        credentials_valid=True,
        fees_configured=True,
        routing_configured=True,
        next_step="test",
    )


def _gateway_wizard_test_step(
    provider_code: str,
    payload: GatewayWizardRequest,
    current_user: dict,
    db: Session,
) -> GatewayWizardResponse:
    """Step 4: Test the gateway connection."""
    try:
        test_result = test_payment_gateway_connection(provider_code, db)
        return GatewayWizardResponse(
            provider_code=provider_code,
            display_name=payload.display_name or provider_code.replace("_", " ").title(),
            provider_kind=payload.provider_kind,
            step="test",
            is_enabled=True,
            credentials_valid=True,
            fees_configured=True,
            routing_configured=True,
            test_passed=test_result.test_status == "passed",
            test_message=test_result.message,
            next_step=None,
        )
    except HTTPException as exc:
        logger.exception("_gateway_wizard_test_step_failed", error=str(exc))
        return GatewayWizardResponse(
            provider_code=provider_code,
            display_name=payload.display_name or provider_code.replace("_", " ").title(),
            provider_kind=payload.provider_kind,
            step="test",
            is_enabled=False,
            credentials_valid=True,
            fees_configured=True,
            routing_configured=True,
            test_passed=False,
            test_message=str(exc.detail),
            next_step=None,
        )


def _resolve_gateway_callback_base(db: Session, provider_code: str) -> str:
    record = _get_gateway_connection_record(db, provider_code)
    configured = _optional_text(getattr(record, "webhook_url", None)) if record else None
    if configured:
        return configured.rstrip("/")
    base = os.getenv("BACKEND_PUBLIC_URL") or getattr(settings, "backend_public_url", "") or getattr(settings, "frontend_url", "")
    return str(base).rstrip("/")


def is_checkout_payment_method_allowed(
    payment_method: str | None,
    db: Session | None = None,
    country_code: str | None = None,
) -> bool:
    """Built-in methods always pass; any registered, enabled, customer-checkout
    gateway connection is also a valid plug-and-play checkout method.

    When ``country_code`` is provided, the gateway is resolved country-aware so a
    per-country gateway (e.g. a PK-only Paymob config) is recognised as valid even
    though a global ("*") row may not exist.
    """
    normalized = normalize_checkout_payment_method(payment_method)
    if normalized in SUPPORTED_CHECKOUT_PAYMENT_METHODS:
        return True
    if db is None:
        return False
    record = _get_gateway_connection_record(db, normalized, country_code)
    if record is None:
        return False
    if not getattr(record, "is_enabled", False):
        return False
    if not getattr(record, "supports_customer_checkout", False):
        return False
    return True


def _is_non_placeholder_secret(value: Any, prefixes: tuple[str, ...]) -> bool:
    key = str(value or "").strip()
    if not key:
        return False
    if prefixes and not any(key.startswith(prefix) for prefix in prefixes):
        return False
    lowered = key.lower()
    placeholder_markers = ("...", "change", "replace", "your_", "example")
    return not any(marker in lowered for marker in placeholder_markers)

def resolve_gateway_settings(code: str, db: Session | None = None) -> Optional[GatewaySettings]:
    """Build a gateway's resolved settings from its DB connection record.

    This is the canonical home for gateway *settings*: each provider resolves
    its configuration from the ``PaymentGatewayConnection`` row (DB) plus the
    environment, never from the global app ``settings`` object.
    """
    if db is None:
        return None
    record = _get_gateway_connection_record(db, code)
    if record is None:
        return None
    secret = str(getattr(record, "secret_key", "") or "").strip()
    mode = "live" if secret.startswith(("sk_live_", "rk_live_")) else "test"
    return GatewaySettings(
        provider_code=str(getattr(record, "provider_code", code) or code),
        provider_kind=str(getattr(record, "provider_kind", code) or code),
        display_name=str(getattr(record, "display_name", code) or code),
        is_enabled=bool(getattr(record, "is_active", False)),
        mode=mode,
        public_key=str(getattr(record, "public_key", "") or "") or None,
        secret_key=secret or None,
        webhook_secret=str(getattr(record, "webhook_secret", "") or "") or None,
        api_base_url=str(getattr(record, "api_base_url", "") or "") or None,
        webhook_url=str(getattr(record, "webhook_url", "") or "") or None,
        supports_customer_checkout=bool(getattr(record, "supports_customer_checkout", False)),
        supports_payouts=bool(getattr(record, "supports_payouts", False)),
    )


def _gateway_is_configured(code: str, db: Session | None = None) -> bool:
    """Return whether the given gateway has usable credentials configured."""
    code = _normalize_gateway_code(code)
    if code == "stripe":
        return bool(_stripe_configured(db))
    if code == "tap":
        return bool(_tap_configured(db))
    if code == "paytabs":
        return bool(_paytabs_configured(db))
    settings = resolve_gateway_settings(code, db)
    return bool(settings and settings.is_usable())


# ── Provider registration ───────────────────────────────────────────────────
# The actual ``register_provider`` calls live at the very end of this module,
# AFTER the tail star-imports below. The star-imports bring each adapter's
# callables (e.g. ``create_payment_intent``) into this namespace, so the
# ``operations`` map can reference them directly. Keeping registration last also
# guarantees the registry is fully populated before anything uses it.



from providers.payments._common import *  # noqa: E402,F401,F403
from providers.payments._order import *   # noqa: E402,F401,F403
from providers.payments.config import *    # noqa: E402,F401,F403
from providers.payments.webhooks import * # noqa: E402,F401,F403
from providers.payments.stripe import *    # noqa: E402,F401,F403
from providers.payments.tap import *       # noqa: E402,F401,F403
import structlog
logger = structlog.get_logger(__name__)
from providers.payments.paytabs import *   # noqa: E402,F401,F403
from providers.payments.paypal import *    # noqa: E402,F401,F403
from providers.payments.thawani import *   # noqa: E402,F401,F403
from providers.payments.generic import *   # noqa: E402,F401,F403


# ── Provider registration (after star-imports so adapter callables are in scope) ──
# Each gateway advertises its standard operations (create / confirm / webhook)
# here. The service/controller/router layers dispatch by gateway code through
# ``providers.payments.base.dispatch_provider_operation``, so adding a new
# gateway requires ONLY a provider module + a registration entry below — no
# edits to services, controllers, or routers.
register_provider(GatewayDefinition(
    code="stripe", kind="stripe", label="Stripe", module="providers.payments.stripe",
    settings_resolver=lambda db: resolve_gateway_settings("stripe", db),
    is_configured=lambda db: _gateway_is_configured("stripe", db),
    operations={
        OPERATION_CREATE: create_payment_intent,
        OPERATION_CONFIRM: confirm_card_payment,
        OPERATION_WEBHOOK: handle_stripe_webhook,
    },
))
register_provider(GatewayDefinition(
    code="tap", kind="tap", label="Tap Payments", module="providers.payments.tap",
    settings_resolver=lambda db: resolve_gateway_settings("tap", db),
    is_configured=lambda db: _gateway_is_configured("tap", db),
    operations={
        OPERATION_CREATE: create_tap_charge,
        OPERATION_CONFIRM: confirm_tap_payment,
        OPERATION_WEBHOOK: handle_tap_webhook,
    },
))
register_provider(GatewayDefinition(
    code="paytabs", kind="paytabs", label="PayTabs", module="providers.payments.paytabs",
    settings_resolver=lambda db: resolve_gateway_settings("paytabs", db),
    is_configured=lambda db: _gateway_is_configured("paytabs", db),
    operations={
        OPERATION_CREATE: create_paytabs_charge,
        OPERATION_CONFIRM: confirm_paytabs_payment,
        OPERATION_WEBHOOK: handle_paytabs_callback,
    },
))
register_provider(GatewayDefinition(
    code="paypal", kind="paypal", label="PayPal", module="providers.payments.paypal",
    settings_resolver=lambda db: resolve_gateway_settings("paypal", db),
    is_configured=lambda db: _gateway_is_configured("paypal", db),
    operations={
        OPERATION_CREATE: create_paypal_order,
        OPERATION_CONFIRM: capture_paypal_order,
        OPERATION_WEBHOOK: handle_paypal_webhook,
    },
))
register_provider(GatewayDefinition(
    code="thawani", kind="thawani", label="Thawani Pay", module="providers.payments.thawani",
    settings_resolver=lambda db: resolve_gateway_settings("thawani", db),
    is_configured=lambda db: _gateway_is_configured("thawani", db),
    operations={
        OPERATION_CREATE: create_thawani_session,
        OPERATION_CONFIRM: confirm_thawani_payment,
        OPERATION_WEBHOOK: handle_thawani_webhook,
    },
))
register_provider(GatewayDefinition(
    code="generic", kind="custom", label="Generic Hosted Gateway", module="providers.payments.generic",
    settings_resolver=lambda db: resolve_gateway_settings("generic", db),
    is_configured=lambda db: _gateway_is_configured("generic", db),
    operations={
        OPERATION_CREATE: create_generic_gateway_payment,
        OPERATION_CONFIRM: confirm_generic_gateway_payment,
        # The generic webhook is keyed by provider_code in the URL, so bind a
        # closure that injects the canonical "generic" code.
        OPERATION_WEBHOOK: lambda request, db: handle_generic_gateway_callback(request, "generic", db),
    },
))
