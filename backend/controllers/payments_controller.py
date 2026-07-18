"""
Payments Controller — Stripe and Tap Payments business logic.

Security hardening applied:
  - Stripe webhooks: verified via stripe.Webhook.construct_event (existing)
  - Tap webhooks: verified via HMAC-SHA256 of the raw request body using
    TAP_WEBHOOK_SECRET (new).  Requests without a valid signature are rejected
    with HTTP 400.
  - Both processors use ProcessedWebhookEvent for idempotency.
  - sales_count is incremented on every item when a payment succeeds.
  - All Tap config (key, webhook secret, webhook URL) is read from settings,
    not bare os.getenv(), so they are validated at startup and appear in docs.
"""
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

from models import Coupon, Order, OrderItem, Payment, PaymentGatewayConnection, PaymentProviderConfig, Product, Notification, ProcessedWebhookEvent, TransactionLedger, CountryConfig
from utils.config import settings
from controllers.products_controller import _bump_product_cache_version
from utils.currency import (
    convert_from_aed,
    get_currency_context,
    money_to_minor_units_for_currency,
)

logger = logging.getLogger(__name__)

stripe.api_key = str(getattr(settings, "stripe_secret_key", "") or "").strip()
if str(getattr(settings, "stripe_api_version", "") or "").strip():
    stripe.api_version = str(getattr(settings, "stripe_api_version", "") or "").strip()

LOW_STOCK_THRESHOLD = 5
INVENTORY_RELEASE_STATUSES = {"cancelled", "refunded"}
INVENTORY_HELD_STATUSES = {"confirmed", "processing", "prepared", "picking_up", "shipped", "delivered"}
COD_PAYMENT_METHOD = "cod"
PAYTABS_PAYMENT_METHOD = "paytabs"
THAWANI_PAYMENT_METHOD = "thawani"
REUSABLE_STRIPE_INTENT_STATUSES = {
    "requires_payment_method",
    "requires_confirmation",
    "requires_action",
    "processing",
    "requires_capture",
}
SUPPORTED_CHECKOUT_PAYMENT_METHODS = {COD_PAYMENT_METHOD, "card", "tap", PAYTABS_PAYMENT_METHOD, THAWANI_PAYMENT_METHOD}
ORDER_PAYMENT_METHOD_GATEWAY_MAP = {"card": "stripe", "tap": "tap", PAYTABS_PAYMENT_METHOD: PAYTABS_PAYMENT_METHOD, THAWANI_PAYMENT_METHOD: THAWANI_PAYMENT_METHOD}
ONLINE_PAYMENT_PROVIDER_MODES = {"stripe", "tap", "both"}
SUPPORTED_GATEWAY_KINDS = {"stripe", "tap", "custom"}
SUPPORTED_GATEWAY_TEST_STATUSES = {"untested", "passed", "failed"}
SUPPORTED_SETTLEMENT_CYCLES = {"daily", "weekly", "monthly"}
DEFAULT_SETTLEMENT_CYCLE = "weekly"
BUILT_IN_GATEWAY_ORDER = ("stripe", "tap", PAYTABS_PAYMENT_METHOD, "paypal", "hyperpay", "omannet", THAWANI_PAYMENT_METHOD)
BUILT_IN_GATEWAY_CODES = set(BUILT_IN_GATEWAY_ORDER)
LIVE_ADAPTER_GATEWAY_CODES = {"stripe", "tap", PAYTABS_PAYMENT_METHOD, "paypal", THAWANI_PAYMENT_METHOD}
DEFAULT_TAP_API_BASE_URL = "https://api.tap.company"
DEFAULT_TAP_TEST_CHARGE_ID = "chg_test_connection_check"
DEFAULT_PAYTABS_API_BASE_URL = "https://secure.paytabs.com"
DEFAULT_PAYPAL_SANDBOX_URL = "https://api-m.sandbox.paypal.com"
DEFAULT_PAYPAL_LIVE_URL = "https://api-m.paypal.com"
DEFAULT_THAWANI_UAT_URL = "https://uatcheckout.thawani.om/api/v1"
DEFAULT_THAWANI_LIVE_URL = "https://checkout.thawani.om/api/v1"
DEFAULT_THAWANI_UAT_PAY_BASE = "https://uatcheckout.thawani.om"
DEFAULT_THAWANI_LIVE_PAY_BASE = "https://checkout.thawani.om"
DEFAULT_PAYTABS_REQUEST_PATH = "/payment/request"
DEFAULT_PAYTABS_QUERY_PATH = "/payment/query"
PAYTABS_SUCCESS_RESPONSE_STATUSES = {"a", "approved", "success", "captured"}
PAYTABS_PENDING_RESPONSE_STATUSES = {"h", "hold", "pending", "p", "processing"}
PAYTABS_FAILURE_RESPONSE_STATUSES = {"d", "declined", "e", "error", "failed"}
TAP_COUNTRY_DIAL_CODES = {
    "AE": "971",
    "BH": "973",
    "EG": "20",
    "GB": "44",
    "JO": "962",
    "KW": "965",
    "OM": "968",
    "QA": "974",
    "SA": "966",
    "US": "1",
}


# ── Pydantic request models ───────────────────────────────────────────────────

class PaymentIntentRequest(BaseModel):
    amount: Optional[int] = None
    currency: Optional[str] = None
    country: Optional[str] = None
    order_id: Optional[int] = None


class StripeCheckoutSessionRequest(BaseModel):
    currency: Optional[str] = None
    country: Optional[str] = None
    order_id: Optional[int] = None
    success_url: str = ""
    cancel_url: str = ""

    def model_post_init(self, __context: object) -> None:  # noqa: D401
        if not self.success_url and self.order_id is not None:
            self.success_url = f"{settings.frontend_url}/checkout?stripe_order_id={self.order_id}&stripe_checkout_session_id={{CHECKOUT_SESSION_ID}}"
        if not self.cancel_url:
            self.cancel_url = f"{settings.frontend_url}/checkout"


class ConfirmCardPaymentRequest(BaseModel):
    order_id: int
    payment_intent_id: Optional[str] = None
    checkout_session_id: Optional[str] = None


class ConfirmTapPaymentRequest(BaseModel):
    order_id: int
    charge_id: Optional[str] = None


class ConfirmPayTabsPaymentRequest(BaseModel):
    order_id: int
    tran_ref: Optional[str] = None


class TapChargeRequest(BaseModel):
    amount: Optional[float] = None
    currency: Optional[str] = None
    country: Optional[str] = None
    description: str = "ZOZI Purchase"
    order_id: Optional[int] = None
    success_url: str = ""
    cancel_url: str = ""

    def model_post_init(self, __context: object) -> None:  # noqa: D401
        """Set URL defaults from settings after model is constructed."""
        if not self.success_url:
            self.success_url = f"{settings.frontend_url}/orders"
        if not self.cancel_url:
            self.cancel_url = f"{settings.frontend_url}/checkout"


class PayTabsChargeRequest(BaseModel):
    amount: Optional[float] = None
    currency: Optional[str] = None
    country: Optional[str] = None
    description: str = "ZOZI Purchase"
    order_id: Optional[int] = None
    success_url: str = ""
    cancel_url: str = ""

    def model_post_init(self, __context: object) -> None:  # noqa: D401
        if not self.success_url:
            self.success_url = f"{settings.frontend_url}/orders"
        if not self.cancel_url:
            self.cancel_url = f"{settings.frontend_url}/checkout"


class PayPalOrderRequest(BaseModel):
    order_id: Optional[int] = None
    currency: Optional[str] = None
    country: Optional[str] = None
    description: str = "ZOZI Purchase"
    return_url: str = ""
    cancel_url: str = ""

    def model_post_init(self, __context: object) -> None:  # noqa: D401
        if not self.return_url:
            self.return_url = f"{settings.frontend_url}/orders"
        if not self.cancel_url:
            self.cancel_url = f"{settings.frontend_url}/checkout"


class PayPalCaptureRequest(BaseModel):
    order_id: int
    paypal_order_id: str


class ThawaniCheckoutRequest(BaseModel):
    order_id: Optional[int] = None
    currency: Optional[str] = None
    country: Optional[str] = None
    description: str = "ZOZI Purchase"
    success_url: str = ""
    cancel_url: str = ""

    def model_post_init(self, __context: object) -> None:  # noqa: D401
        if not self.success_url:
            self.success_url = f"{settings.frontend_url}/orders"
        if not self.cancel_url:
            self.cancel_url = f"{settings.frontend_url}/checkout"


class PaymentMethodsStatus(BaseModel):
    cod: dict
    card: dict
    tap: dict
    paytabs: dict


class PaymentProviderRuntimeConfigRequest(BaseModel):
    online_provider: Literal["stripe", "tap", "both"]


class PaymentProviderRuntimeConfigResponse(BaseModel):
    id: Optional[int] = None
    online_provider: Literal["stripe", "tap", "both"]
    source: str
    stripe_configured: bool
    tap_configured: bool
    stripe_enabled: bool
    tap_enabled: bool
    enabled_processors: list[str]
    can_accept_online_payments: bool
    updated_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class PaymentGatewayConnectionRequest(BaseModel):
    provider_code: str
    provider_kind: Literal["stripe", "tap", "custom"] = "custom"
    display_name: str
    # Country scope for this gateway connection. Use "*" (the default) for a
    # global gateway available in every country, or a specific ISO country code
    # (e.g. "PK", "OM", "AE") to make the gateway available only in that country.
    # The same provider_code can be attached per-country (one row per country).
    country_code: str = "*"
    is_enabled: bool = True
    supports_customer_checkout: bool = False
    supports_payouts: bool = False
    mode: Literal["test", "live"] = "test"
    public_key: Optional[str] = None
    secret_key: Optional[str] = None
    webhook_secret: Optional[str] = None
    merchant_id: Optional[str] = None
    api_base_url: Optional[str] = None
    webhook_url: Optional[str] = None
    test_url: Optional[str] = None
    supported_currencies: list[str] = []
    extra_config: dict[str, Any] = {}
    notes: Optional[str] = None
    fee_percent: Decimal = Decimal("0")
    fixed_fee_amount: Decimal = Decimal("0")
    payout_fee_percent: Decimal = Decimal("0")
    payout_fixed_fee_amount: Decimal = Decimal("0")
    pass_fee_to_customer: bool = False
    settlement_cycle: Literal["daily", "weekly", "monthly"] = "weekly"

    def model_post_init(self, __context: object) -> None:  # noqa: D401
        self.provider_code = _normalize_gateway_code(self.provider_code)
        self.display_name = str(self.display_name or "").strip() or self.provider_code.replace("_", " ").title()
        self.public_key = _optional_text(self.public_key)
        self.secret_key = _optional_text(self.secret_key)
        self.webhook_secret = _optional_text(self.webhook_secret)
        self.merchant_id = _optional_text(self.merchant_id)
        self.api_base_url = _optional_text(self.api_base_url)
        self.webhook_url = _optional_text(self.webhook_url)
        self.test_url = _optional_text(self.test_url)
        self.notes = _optional_text(self.notes)
        self.supported_currencies = _normalize_currency_codes(self.supported_currencies)
        self.extra_config = self.extra_config if isinstance(self.extra_config, dict) else {}


class PaymentGatewayConnectionResponse(BaseModel):
    id: Optional[int] = None
    provider_code: str
    provider_kind: Literal["stripe", "tap", "custom"]
    display_name: str
    adapter_supported: bool
    is_enabled: bool
    supports_customer_checkout: bool
    supports_payouts: bool
    mode: Literal["test", "live"]
    country_code: str = "*"
    source: str
    public_key: Optional[str] = None
    merchant_id: Optional[str] = None
    api_base_url: Optional[str] = None
    webhook_url: Optional[str] = None
    test_url: Optional[str] = None
    supported_currencies: list[str]
    extra_config: dict[str, Any]
    notes: Optional[str] = None
    fee_percent: float
    fixed_fee_amount: float
    payout_fee_percent: float
    payout_fixed_fee_amount: float
    pass_fee_to_customer: bool
    settlement_cycle: Literal["daily", "weekly", "monthly"]
    secret_key_configured: bool
    webhook_secret_configured: bool
    test_status: Literal["untested", "passed", "failed"]
    test_message: Optional[str] = None
    last_tested_at: Optional[datetime] = None
    updated_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class PaymentGatewayTestResponse(BaseModel):
    provider_code: str
    test_status: Literal["passed", "failed"]
    message: str
    tested_at: datetime


class GatewayWizardRequest(BaseModel):
    """Request model for the Admin Gateway Wizard."""
    step: Literal["credentials", "fees", "routing", "test"]
    provider_code: str
    display_name: Optional[str] = None
    provider_kind: Literal["stripe", "tap", "custom"] = "custom"
    
    public_key: Optional[str] = None
    secret_key: Optional[str] = None
    webhook_secret: Optional[str] = None
    merchant_id: Optional[str] = None
    api_base_url: Optional[str] = None
    
    fee_percent: Decimal = Decimal("0")
    fixed_fee_amount: Decimal = Decimal("0")
    pass_fee_to_customer: bool = False
    
    routing_rules: dict[str, Any] = {}
    priority_tier: int = 1


class GatewayWizardResponse(BaseModel):
    """Response model for the Admin Gateway Wizard."""
    provider_code: str
    display_name: str
    provider_kind: str
    step: str
    is_enabled: bool = False
    credentials_valid: bool = False
    fees_configured: bool = False
    routing_configured: bool = False
    test_passed: bool = False
    test_message: Optional[str] = None
    next_step: Optional[str] = None


class PaymentFinanceQuoteRequest(BaseModel):
    gateway_code: Optional[str] = None
    subtotal_amount: Decimal = Decimal("0")
    discount_amount: Decimal = Decimal("0")
    shipping_amount: Decimal = Decimal("0")
    vat_amount: Decimal = Decimal("0")


class PaymentFinanceQuoteResponse(BaseModel):
    gateway_code: Optional[str] = None
    gateway_display_name: Optional[str] = None
    adapter_supported: bool
    order_total: float
    gateway_fee_amount: float
    customer_payable_total: float
    processor_net_capture: float
    taxable_product_amount: float
    zozi_commission_amount: float
    supplier_payout_estimate: float
    logistics_payout_estimate: float
    estimated_payout_cost: float
    platform_net_after_gateway_and_payout_costs: float
    pass_fee_to_customer: bool


# ── Config helpers ────────────────────────────────────────────────────────────

def _optional_text(value: Any) -> Optional[str]:
    normalized = str(value or "").strip()
    return normalized or None


def _normalize_gateway_code(value: str) -> str:
    candidate = "".join(ch.lower() if ch.isalnum() else "_" for ch in str(value or "").strip())
    while "__" in candidate:
        candidate = candidate.replace("__", "_")
    candidate = candidate.strip("_")
    return candidate or "custom_gateway"


def _normalize_currency_codes(values: list[str] | tuple[str, ...] | None) -> list[str]:
    seen: list[str] = []
    for value in values or []:
        code = str(value or "").strip().upper()
        if len(code) != 3 or not code.isalpha() or code in seen:
            continue
        seen.append(code)
    return seen


def _decimal_from_value(value: Any) -> Decimal:
    try:
        return Decimal(str(value or 0))
    except Exception:
        return Decimal("0")


def _float_money(value: Any) -> float:
    return float(_decimal_from_value(value))


def _json_load_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    raw = _optional_text(value)
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _json_load_currency_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return _normalize_currency_codes([str(item) for item in value])
    raw = _optional_text(value)
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except Exception:
        return []
    return _normalize_currency_codes([str(item) for item in parsed]) if isinstance(parsed, list) else []


def _is_non_placeholder_secret(value: Any, prefixes: tuple[str, ...]) -> bool:
    key = str(value or "").strip()
    if not key:
        return False
    if prefixes and not any(key.startswith(prefix) for prefix in prefixes):
        return False
    lowered = key.lower()
    placeholder_markers = ("...", "change", "replace", "your_", "example")
    return not any(marker in lowered for marker in placeholder_markers)


def _gateway_adapter_supported(provider_kind: str, provider_code: str) -> bool:
    normalized_code = _normalize_gateway_code(provider_code)
    return normalized_code in LIVE_ADAPTER_GATEWAY_CODES


def normalize_checkout_payment_method(value: str | None) -> str:
    normalized = str(value or "card").strip().lower()
    if normalized == "stripe":
        return "card"
    return normalized


def gateway_code_for_payment_method(payment_method: str | None) -> Optional[str]:
    return ORDER_PAYMENT_METHOD_GATEWAY_MAP.get(normalize_checkout_payment_method(payment_method))


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


def _verify_paytabs_signature(payload: bytes, signature: str, webhook_secret: str) -> bool:
    if not webhook_secret or not signature:
        return False
    expected = hmac.new(
        webhook_secret.encode("utf-8"),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected)


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


def _normalized_payment_method(order: Order) -> str:
    return str(getattr(order, "payment_method", "card") or "card").strip().lower()


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
    except Exception:
        return None


def _paytabs_checkout_enabled(db: Session) -> bool:
    configured, _, _ = _paytabs_configured(db)
    gateway = _serialize_gateway_connection(PAYTABS_PAYMENT_METHOD, db, _get_gateway_connection_record(db, PAYTABS_PAYMENT_METHOD))
    return configured and gateway.is_enabled and gateway.supports_customer_checkout and gateway.adapter_supported


def _paypal_configured(db: Session) -> tuple[bool, Optional[str], Optional[str], str]:
    """Return (configured, client_id, secret, base_url) for the saved PayPal gateway connection."""
    record = _get_gateway_connection_record(db, "paypal")
    if not record:
        return False, None, None, DEFAULT_PAYPAL_SANDBOX_URL
    client_id = decrypt_secret(cast(str | None, getattr(record, "public_key", None)))
    secret = decrypt_secret(cast(str | None, getattr(record, "secret_key", None)))
    mode = str(getattr(record, "mode", "test") or "test").strip().lower()
    base_url = DEFAULT_PAYPAL_LIVE_URL if mode == "live" else DEFAULT_PAYPAL_SANDBOX_URL
    if not client_id or not secret:
        return False, None, None, base_url
    return True, client_id, secret, base_url


def _paypal_gateway_enabled(db: Session) -> bool:
    configured, _, _, _ = _paypal_configured(db)
    if not configured:
        return False
    gateway = _serialize_gateway_connection("paypal", db, _get_gateway_connection_record(db, "paypal"))
    return gateway.is_enabled and gateway.supports_customer_checkout and gateway.adapter_supported


async def _paypal_get_access_token(client_id: str, secret: str, base_url: str) -> str:
    """Fetch a short-lived OAuth2 client-credentials access token from PayPal."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            f"{base_url}/v1/oauth2/token",
            headers={"Accept": "application/json", "Accept-Language": "en_US"},
            auth=(client_id, secret),
            data={"grant_type": "client_credentials"},
        )
    if resp.status_code != 200:
        logger.error("PayPal token request failed (%s): %s", resp.status_code, resp.text[:200])
        raise HTTPException(status_code=503, detail="PayPal authentication failed")
    token = resp.json().get("access_token")
    if not token:
        raise HTTPException(status_code=503, detail="PayPal authentication failed: no token returned")
    return str(token)


# ── Thawani resolver helpers ──────────────────────────────────────────────────

def _resolve_thawani_secret_key(db: Session | None = None) -> str:
    if db is not None:
        record = _get_gateway_connection_record(db, THAWANI_PAYMENT_METHOD)
        if record:
            raw = decrypt_secret(cast(str | None, getattr(record, "secret_key", None)))
            if raw:
                return raw.strip()
    return str(getattr(settings, "thawani_secret_key", "") or "").strip()


def _resolve_thawani_publishable_key(db: Session | None = None) -> str:
    if db is not None:
        record = _get_gateway_connection_record(db, THAWANI_PAYMENT_METHOD)
        if record:
            raw = decrypt_secret(cast(str | None, getattr(record, "public_key", None)))
            if raw:
                return raw.strip()
    return str(getattr(settings, "thawani_publishable_key", "") or "").strip()


def _resolve_thawani_api_base_url(db: Session | None = None) -> str:
    if db is not None:
        record = _get_gateway_connection_record(db, THAWANI_PAYMENT_METHOD)
        configured_url = _optional_text(getattr(record, "api_base_url", None)) if record else None
        if configured_url:
            return configured_url.rstrip("/")
    return DEFAULT_THAWANI_UAT_URL


def _resolve_thawani_webhook_secret(db: Session | None = None) -> str:
    if db is not None:
        record = _get_gateway_connection_record(db, THAWANI_PAYMENT_METHOD)
        if record:
            raw = decrypt_secret(cast(str | None, getattr(record, "webhook_secret", None)))
            if raw:
                return raw.strip()
    return str(getattr(settings, "thawani_webhook_secret", "") or "").strip()


def _thawani_configured(db: Session | None = None) -> tuple[bool, str, str, str]:
    """Return (configured, secret_key, publishable_key, api_base_url)."""
    secret_key = _resolve_thawani_secret_key(db)
    publishable_key = _resolve_thawani_publishable_key(db)
    api_base_url = _resolve_thawani_api_base_url(db)
    return bool(secret_key and publishable_key), secret_key, publishable_key, api_base_url


def _thawani_checkout_enabled(db: Session) -> bool:
    configured, _, _, _ = _thawani_configured(db)
    gateway = _serialize_gateway_connection(THAWANI_PAYMENT_METHOD, db, _get_gateway_connection_record(db, THAWANI_PAYMENT_METHOD))
    return configured and gateway.is_enabled and gateway.supports_customer_checkout and gateway.adapter_supported


def _order_holds_inventory(order: Order) -> bool:
    # Inventory is reserved at payment confirmation (via _finalize_inventory_for_paid_order),
    # not at order creation.  Only orders that have been confirmed/paid and not yet
    # cancelled/refunded still hold stock.
    order_status = cast(str, getattr(order, "status", ""))
    return order_status in INVENTORY_HELD_STATUSES


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
        status = "failed"
        message = str(exc.detail)
    except Exception as exc:
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


def _get_user_order(order_id: Optional[int], current_user: dict, db: Session) -> Order:
    if not order_id:
        raise HTTPException(status_code=422, detail="order_id is required")

    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == current_user["id"],
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


def _resolved_payment_currency(currency: str | None, country: str | None) -> str:
    context = get_currency_context(country=country, currency=currency, default_currency="AED")
    return str(context["currency_code"])


def _extract_order_customer_name(order: Order) -> str:
    shipping_address = str(getattr(order, "shipping_address", "") or "").strip()
    if not shipping_address:
        return ""

    first_segment = shipping_address.split(",", 1)[0].strip()
    if not first_segment:
        return ""

    # Shipping addresses stored by the checkout flow start with the customer's
    # full name. Guard against legacy test payloads that only store a street.
    if first_segment[0].isdigit():
        return ""

    return first_segment


def _split_customer_name(full_name: str) -> tuple[str, str]:
    normalized = " ".join(part for part in full_name.split() if part)
    if not normalized:
        return ("Customer", "ZOZI")

    parts = normalized.split(" ", 1)
    if len(parts) == 1:
        return (parts[0], "ZOZI")

    return (parts[0], parts[1])


def _tap_country_dial_code(country: str | None) -> str:
    code = "".join(ch for ch in str(country or "").upper() if ch.isalpha())[:2]
    return TAP_COUNTRY_DIAL_CODES.get(code, "")


def _tap_phone_payload(phone_value: str | None, country: str | None) -> dict[str, str] | None:
    digits = "".join(ch for ch in str(phone_value or "") if ch.isdigit())
    if not digits:
        return None

    if digits.startswith("00"):
        digits = digits[2:]

    dial_code = _tap_country_dial_code(country)
    if not dial_code:
        return None

    if digits.startswith(dial_code):
        digits = digits[len(dial_code):]

    digits = digits.lstrip("0")
    if not digits:
        return None

    return {
        "country_code": dial_code,
        "number": digits,
    }


def _build_tap_customer(order: Order, current_user: dict[str, Any]) -> dict[str, Any]:
    full_name = _extract_order_customer_name(order)
    if not full_name:
        username = str(current_user.get("username") or "").strip()
        if username and "@" not in username:
            full_name = username.replace(".", " ").replace("_", " ")

    if not full_name:
        email_local = str(current_user.get("email") or "").split("@", 1)[0].strip()
        if email_local:
            full_name = email_local.replace(".", " ").replace("_", " ")

    first_name, last_name = _split_customer_name(full_name)
    customer: dict[str, Any] = {
        "first_name": first_name,
        "last_name": last_name,
    }

    email = str(current_user.get("email") or "").strip()
    if email:
        customer["email"] = email

    phone_payload = _tap_phone_payload(
        cast(str | None, getattr(order, "customer_phone", None)) or cast(str | None, current_user.get("phone")),
        cast(str | None, getattr(order, "shipping_country", None)) or cast(str | None, current_user.get("preferred_country")),
    )
    if phone_payload:
        customer["phone"] = phone_payload

    if "email" not in customer and "phone" not in customer:
        raise HTTPException(status_code=422, detail="Customer email or phone is required for Tap payments")

    return customer


def _order_charge_total_amount(order: Order) -> Decimal:
    return max(
        _decimal_from_value(getattr(order, "payment_customer_total_amount", None) or getattr(order, "total_amount", 0)),
        Decimal("0"),
    )


def _order_gateway_metadata(order: Order) -> dict[str, str]:
    return {
        "gateway_code": str(getattr(order, "payment_gateway_code", "") or "").strip(),
        "gateway_fee_amount": str(_decimal_from_value(getattr(order, "payment_gateway_fee_amount", 0))),
        "customer_total_amount": str(_order_charge_total_amount(order)),
    }


def _paytabs_customer_details(order: Order, current_user: dict[str, Any]) -> dict[str, Any]:
    full_name = _extract_order_customer_name(order) or str(current_user.get("username") or "Customer").replace("_", " ").replace(".", " ")
    email = str(current_user.get("email") or "customer@zozi.local").strip() or "customer@zozi.local"
    phone = "".join(ch for ch in str(getattr(order, "customer_phone", None) or current_user.get("phone") or "") if ch.isdigit())
    country = str(getattr(order, "shipping_country", "") or "AE").strip().upper() or "AE"
    city = str(getattr(order, "shipping_city", "") or "Dubai").strip() or "Dubai"
    postal_code = str(getattr(order, "shipping_postal_code", "") or "00000").strip() or "00000"
    street = str(getattr(order, "shipping_address", "") or "ZOZI").strip() or "ZOZI"
    return {
        "name": full_name,
        "email": email,
        "phone": phone,
        "street1": street[:120],
        "city": city,
        "state": city,
        "country": country,
        "zip": postal_code,
    }


def _paytabs_shipping_details(order: Order, current_user: dict[str, Any]) -> dict[str, Any]:
    return _paytabs_customer_details(order, current_user)


def _paytabs_transaction_reference(payload: dict[str, Any]) -> str:
    payment_result = payload.get("payment_result") if isinstance(payload.get("payment_result"), dict) else {}
    for key in ("tran_ref", "transaction_reference"):
        value = payload.get(key) or payment_result.get(key)
        if value:
            return str(value).strip()
    return ""


def _paytabs_response_status(payload: dict[str, Any]) -> str:
    payment_result = payload.get("payment_result") if isinstance(payload.get("payment_result"), dict) else {}
    for key in ("response_status", "payment_status", "tran_status"):
        value = payment_result.get(key) or payload.get(key)
        if value:
            return str(value).strip().lower()
    return ""


def _paytabs_response_message(payload: dict[str, Any]) -> str:
    payment_result = payload.get("payment_result") if isinstance(payload.get("payment_result"), dict) else {}
    for key in ("response_message", "message"):
        value = payment_result.get(key) or payload.get(key)
        if value:
            return str(value).strip()
    return "PayTabs payment verification failed"


def _stripe_object_get(obj: Any, key: str, default: Any = None) -> Any:
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)

    value = getattr(obj, key, None)
    if value is not None:
        return value

    getter = getattr(obj, "get", None)
    if callable(getter):
        try:
            return getter(key, default)
        except Exception:
            return default
    return default


def _stripe_metadata_map(obj: Any) -> dict[str, str]:
    raw_metadata = _stripe_object_get(obj, "metadata", {}) or {}
    if isinstance(raw_metadata, dict):
        items = raw_metadata.items()
    else:
        items_fn = getattr(raw_metadata, "items", None)
        if callable(items_fn):
            try:
                items = items_fn()
            except Exception:
                items = []
        else:
            items = []

    metadata: dict[str, str] = {}
    for key, value in items:
        if value is None:
            continue
        metadata[str(key)] = str(value)
    return metadata


def _payment_intent_status(intent: Any) -> str:
    return str(_stripe_object_get(intent, "status", "") or "").strip().lower()


def _payment_intent_id(intent: Any) -> str:
    return str(_stripe_object_get(intent, "id", "") or "").strip()


def _payment_intent_matches_order(
    intent: Any,
    *,
    order: Order,
    expected_user_id: int,
    require_metadata: bool,
) -> tuple[bool, str]:
    metadata = _stripe_metadata_map(intent)
    metadata_order_id = metadata.get("order_id")
    metadata_user_id = metadata.get("user_id")

    if require_metadata and not metadata_order_id:
        return False, "missing order_id metadata"
    if metadata_order_id and metadata_order_id != str(order.id):
        return False, f"metadata order_id mismatch ({metadata_order_id} != {order.id})"
    if metadata_user_id and metadata_user_id != str(expected_user_id):
        return False, f"metadata user_id mismatch ({metadata_user_id} != {expected_user_id})"

    metadata_amount_minor = metadata.get("zozi_amount_minor")
    intent_amount = _stripe_object_get(intent, "amount", None)
    if metadata_amount_minor and intent_amount is not None:
        try:
            if int(str(intent_amount)) != int(metadata_amount_minor):
                return (
                    False,
                    f"amount mismatch ({intent_amount} != {metadata_amount_minor})",
                )
        except (TypeError, ValueError):
            return False, "invalid payment amount metadata"

    metadata_display_currency = metadata.get("display_currency", "").strip().upper()
    intent_currency = str(_stripe_object_get(intent, "currency", "") or "").strip().upper()
    if metadata_display_currency and intent_currency and metadata_display_currency != intent_currency:
        return (
            False,
            f"currency mismatch ({intent_currency} != {metadata_display_currency})",
        )

    return True, ""


def _mark_coupon_as_used(order: Order, db: Session) -> None:
    coupon_code = cast(Optional[str], getattr(order, "coupon_code", None))
    if not coupon_code:
        return

    coupon = db.query(Coupon).filter(Coupon.code == coupon_code).first()
    if coupon:
        uses_count = cast(Optional[int], getattr(coupon, "uses_count", None))
        setattr(coupon, "uses_count", (uses_count or 0) + 1)


def _increment_sales_counts(order: Order, db: Session) -> None:
    """Increment Product.sales_count for each item in the order."""
    order_items = (
        db.query(OrderItem)
        .filter(OrderItem.order_id == order.id)
        .all()
    )
    if not order_items:
        return
    # Batch-load all products at once
    product_ids = list({cast(int, item.product_id) for item in order_items})
    products_map = {
        cast(int, p.id): p
        for p in db.query(Product).filter(Product.id.in_(product_ids)).all()
    }
    for item in order_items:
        product = products_map.get(cast(int, item.product_id))
        if product:
            sales_count = cast(Optional[int], getattr(product, "sales_count", None))
            quantity = cast(int, getattr(item, "quantity"))
            setattr(product, "sales_count", (sales_count or 0) + quantity)


def _finalize_inventory_for_paid_order(order: Order, db: Session) -> list[str]:
    supplier_notifs: dict[int, list[str]] = {}
    order_items = (
        db.query(OrderItem)
        .filter(OrderItem.order_id == order.id)
        .all()
    )
    requested_quantities: dict[int, int] = {}
    issues: list[str] = []

    for order_item in order_items:
        product_id = cast(int, getattr(order_item, "product_id"))
        quantity = cast(int, getattr(order_item, "quantity"))
        requested_quantities[product_id] = (
            requested_quantities.get(product_id, 0) + quantity
        )

    # Batch-load all products at once instead of one-by-one
    products_by_id: dict[int, Product] = {
        cast(int, p.id): p
        for p in db.query(Product).filter(Product.id.in_(list(requested_quantities.keys()))).all()
    } if requested_quantities else {}

    for product_id, requested_quantity in requested_quantities.items():
        product = products_by_id.get(product_id)
        if not product:
            logger.warning(
                "Payment success inventory finalization skipped missing product: order=%s product=%s",
                order.id,
                product_id,
            )
            issues.append(f"missing_product:{product_id}")
            continue

        products_by_id[product_id] = product

        stock = cast(int, getattr(product, "stock"))

        if stock < requested_quantity:
            logger.warning(
                "Inventory shortfall on payment success: order=%s product=%s available=%s requested=%s",
                order.id,
                product.id,
                stock,
                requested_quantity,
            )
            issues.append(
                f"insufficient_stock:{product.id}:available={stock}:requested={requested_quantity}"
            )

    if issues:
        return issues

    _bump_product_cache_version()
    for product_id, requested_quantity in requested_quantities.items():
        product = products_by_id[product_id]
        stock = cast(int, getattr(product, "stock"))
        new_stock = stock - requested_quantity
        setattr(product, "stock", new_stock)

        supplier_id = cast(Optional[int], getattr(product, "supplier_id", None))
        product_name = cast(str, getattr(product, "name"))
        if supplier_id is not None:
            supplier_notifs.setdefault(supplier_id, []).append(product_name)
            if new_stock <= LOW_STOCK_THRESHOLD:
                db.add(
                    Notification(
                        user_id=supplier_id,
                        type="low_stock",
                        title="Low Stock Alert",
                        message=f'"{product_name}" has only {new_stock} units left.',
                        link="/supplier/inventory",
                    )
                )

    for supplier_id, product_names in supplier_notifs.items():
        names_str = ", ".join(product_names[:3])
        if len(product_names) > 3:
            names_str += f" +{len(product_names) - 3} more"
        db.add(
            Notification(
                user_id=supplier_id,
                type="order_update",
                title="New Order Received",
                message=f"Order #{order.id} includes your product(s): {names_str}.",
                link="/supplier/orders",
            )
        )

    return []


def _restore_inventory_for_order(order: Order, db: Session) -> None:
    order_items = (
        db.query(OrderItem)
        .filter(OrderItem.order_id == order.id)
        .all()
    )

    product_ids = list({oi.product_id for oi in order_items})
    products_by_id = {
        p.id: p
        for p in db.query(Product).filter(Product.id.in_(product_ids)).all()
    } if product_ids else {}

    for order_item in order_items:
        product = products_by_id.get(order_item.product_id)
        if not product:
            logger.warning(
                "Inventory restore skipped missing product: order=%s product=%s",
                order.id,
                order_item.product_id,
            )
            continue

        stock = cast(int, getattr(product, "stock"))
        quantity = cast(int, getattr(order_item, "quantity"))
        setattr(product, "stock", stock + quantity)
    _bump_product_cache_version()


def apply_order_status_change(order: Order, target_status: str, db: Session) -> bool:
    restored_inventory = False
    if (
        _order_holds_inventory(order)
        and target_status in INVENTORY_RELEASE_STATUSES
    ):
        _restore_inventory_for_order(order, db)
        restored_inventory = True

    setattr(order, "status", target_status)

    # ── Cash Management: refund ledger on cancellation/refund ──
    if target_status in ("refunded", "cancelled"):
        try:
            from services.cash_management_service import create_refund_ledger_entry
            reason = "cancellation" if target_status == "cancelled" else "refund"
            create_refund_ledger_entry(order, db, reason=reason)
        except Exception:
            logger.exception("Failed to create refund ledger for order %s", order.id)

    return restored_inventory


def _confirm_order(
    order: Order,
    confirmation_title: str,
    confirmation_message: str,
    db: Session,
    *,
    mark_paid: bool,
) -> None:
    inventory_issues = _finalize_inventory_for_paid_order(order, db)
    if mark_paid:
        setattr(order, "paid_at", datetime.now(timezone.utc))

    if inventory_issues:
        setattr(order, "status", "failed")
        db.add(
            Notification(
                user_id=order.user_id,
                type="order_update",
                title="Order Requires Refund",
                message=(
                    f"Payment for Order #{order.id} was received, but one or more items are no longer available. "
                    "Support will contact you about a refund."
                ),
                link=f"/orders/{order.id}",
            )
        )
        logger.warning(
            "Payment success could not finalize inventory for order %s issues=%s",
            order.id,
            "; ".join(inventory_issues),
        )
        return

    setattr(order, "status", "confirmed")
    _mark_coupon_as_used(order, db)
    _increment_sales_counts(order, db)

    # ── Cash Management: create ledger entries on confirmation ──
    try:
        from services.cash_management_service import create_ledger_entries_for_order, log_card_payment_received
        create_ledger_entries_for_order(order, db)
        # Log card payment into bank transaction ledger
        if mark_paid and _normalized_payment_method(order) != "cod":
            log_card_payment_received(order, db)
    except Exception:
        logger.exception("Failed to create ledger entries for order %s", order.id)

    db.add(
        Notification(
            user_id=order.user_id,
            type="order_update",
            title=confirmation_title,
            message=confirmation_message,
            link=f"/orders/{order.id}",
        )
    )


def _apply_successful_payment(order: Order, confirmation_message: str, db: Session) -> None:
    # Create journal entry for customer payment (Gateway Settlement Receivable -> Deferred Revenue)
    from services.general_ledger_service import post_order_payment_journal
    
    try:
        # Calculate order total amount for the journal entry
        total_amount = order.total_amount if order.total_amount is not None else (
            order.subtotal_amount if order.subtotal_amount is not None else 0
        )
        
        # Post payment journal entry to general ledger
        post_order_payment_journal(db, order.id, total_amount)
    except Exception as e:
        # Log the error but don't fail the payment process
        # The general ledger entry failure should not rollback the payment
        logger.error(f"Failed to create payment journal entry for order {order.id}: {str(e)}")
    
    _confirm_order(
        order,
        "Payment Confirmed",
        confirmation_message,
        db,
        mark_paid=True,
    )

    # Keep the local Payment ledger consistent with the now-confirmed order so
    # that downstream confirm/idempotency checks (which look for a "completed"
    # Payment) behave correctly for every provider, including plug-and-play
    # generic gateways.
    try:
        normalized = _normalized_payment_method(order)
        db.query(Payment).filter(
            Payment.order_id == order.id,
            Payment.provider == normalized,
        ).update({Payment.status: "completed"})
    except Exception:
        logger.exception("Failed to mark Payment rows completed for order %s", order.id)


def confirm_cash_on_delivery_order(order: Order, db: Session) -> None:
    _confirm_order(
        order,
        "Order Confirmed",
        f"Order #{order.id} has been placed with Cash on Delivery. We are preparing your order.",
        db,
        mark_paid=False,
    )


# ── Stripe payment intent ─────────────────────────────────────────────────────

def create_payment_intent(body: PaymentIntentRequest, current_user: dict, db: Session) -> dict:
    if not _stripe_configured(db):
        raise HTTPException(status_code=503, detail="Payment service not configured")
    if not _payment_provider_mode_allows("stripe", db):
        raise HTTPException(status_code=409, detail="Stripe card payments are currently disabled by admin")
    _apply_stripe_runtime_key(db)

    order = _get_user_order(body.order_id, current_user, db)
    if _normalized_payment_method(order) != "card":
        raise HTTPException(status_code=409, detail="This order is not configured for card payment")
    if order.status in INVENTORY_RELEASE_STATUSES:
        raise HTTPException(status_code=409, detail="Order is already closed")
    if order.paid_at is not None:
        raise HTTPException(status_code=409, detail="Order is already paid")
    currency_code = _resolved_payment_currency(body.currency, body.country)
    charge_total = _order_charge_total_amount(order)
    converted_total = convert_from_aed(charge_total, currency_code)
    amount_minor = money_to_minor_units_for_currency(charge_total, currency_code)
    metadata: dict = {"user_id": str(current_user["id"])}
    metadata["order_id"] = str(order.id)
    metadata["base_currency"] = "AED"
    metadata["display_currency"] = currency_code
    metadata["zozi_amount_minor"] = str(amount_minor)
    metadata.update(_order_gateway_metadata(order))
    existing_payment_intent_id = cast(Optional[str], getattr(order, "payment_intent_id", None))

    if existing_payment_intent_id:
        try:
            existing_intent = stripe.PaymentIntent.retrieve(existing_payment_intent_id)
            existing_status = _payment_intent_status(existing_intent)
            existing_currency = str(_stripe_object_get(existing_intent, "currency", "") or "").upper()
            existing_client_secret = cast(Optional[str], _stripe_object_get(existing_intent, "client_secret", None))
            valid_existing, reason = _payment_intent_matches_order(
                existing_intent,
                order=order,
                expected_user_id=int(current_user["id"]),
                require_metadata=False,
            )
            if (
                existing_status in REUSABLE_STRIPE_INTENT_STATUSES
                and existing_currency == currency_code.upper()
                and existing_client_secret
                and valid_existing
            ):
                return {
                    "client_secret": existing_client_secret,
                    "payment_intent_id": _payment_intent_id(existing_intent) or existing_payment_intent_id,
                    "currency": currency_code,
                    "display_amount": float(converted_total),
                }
            if existing_status == "succeeded":
                _apply_successful_payment(
                    order,
                    f"Order #{order.id} payment was successful. We are preparing your order.",
                    db,
                )
                db.commit()
                raise HTTPException(status_code=409, detail="Order is already paid")
            if not valid_existing:
                logger.warning(
                    "Stored payment_intent_id failed validation for order %s: %s",
                    order.id,
                    reason,
                )
        except HTTPException:
            raise
        except Exception as exc:
            if exc.__class__.__module__.startswith("stripe"):
                logger.warning(
                    "Could not reuse Stripe payment intent %s for order %s: %s",
                    existing_payment_intent_id,
                    order.id,
                    getattr(exc, "user_message", str(exc)),
                )
            else:
                raise

    try:
        idempotency_key = (
            f"order:{order.id}:prev:{existing_payment_intent_id or 'none'}:"
            f"currency:{currency_code.lower()}"
        )
        intent = stripe.PaymentIntent.create(
            amount=amount_minor,
            currency=currency_code.lower(),
            automatic_payment_methods={"enabled": True, "allow_redirects": "never"},
            metadata=metadata,
            idempotency_key=idempotency_key,
        )
        setattr(order, "payment_intent_id", intent.id)
        db.commit()
        return {
            "client_secret": intent.client_secret,
            "payment_intent_id": intent.id,
            "currency": currency_code,
            "display_amount": float(converted_total),
        }
    except Exception as exc:
        if exc.__class__.__module__.startswith("stripe"):
            raise HTTPException(status_code=400, detail=str(getattr(exc, "user_message", str(exc))))
        raise HTTPException(status_code=500, detail="Payment service error")


def create_stripe_checkout_session(body: StripeCheckoutSessionRequest, current_user: dict, db: Session) -> dict:
    if not _stripe_configured(db):
        raise HTTPException(status_code=503, detail="Payment service not configured")
    if not _payment_provider_mode_allows("stripe", db):
        raise HTTPException(status_code=409, detail="Stripe card payments are currently disabled by admin")
    _apply_stripe_runtime_key(db)

    order = _get_user_order(body.order_id, current_user, db)
    if _normalized_payment_method(order) != "card":
        raise HTTPException(status_code=409, detail="This order is not configured for card payment")
    if order.status in INVENTORY_RELEASE_STATUSES:
        raise HTTPException(status_code=409, detail="Order is already closed")
    if order.paid_at is not None:
        raise HTTPException(status_code=409, detail="Order is already paid")

    currency_code = _resolved_payment_currency(body.currency, body.country)
    charge_total = _order_charge_total_amount(order)
    converted_total = convert_from_aed(charge_total, currency_code)
    amount_minor = money_to_minor_units_for_currency(charge_total, currency_code)
    metadata: dict[str, str] = {
        "user_id": str(current_user["id"]),
        "order_id": str(order.id),
        "base_currency": "AED",
        "display_currency": currency_code,
        "zozi_amount_minor": str(amount_minor),
        **_order_gateway_metadata(order),
    }

    try:
        session = stripe.checkout.Session.create(
            mode="payment",
            success_url=body.success_url,
            cancel_url=body.cancel_url,
            client_reference_id=str(order.id),
            customer_email=str(current_user.get("email") or "").strip() or None,
            metadata=metadata,
            payment_method_types=["card"],
            line_items=[
                {
                    "quantity": 1,
                    "price_data": {
                        "currency": currency_code.lower(),
                        "unit_amount": amount_minor,
                        "product_data": {
                            "name": f"ZOZI Order #{order.id}",
                            "description": f"Marketplace checkout for order #{order.id}",
                        },
                    },
                }
            ],
        )
        session_id = str(_stripe_object_get(session, "id", "") or "").strip()
        if session_id:
            setattr(order, "payment_intent_id", session_id)
            db.commit()
        return {
            "checkout_session_id": session_id,
            "checkout_url": _stripe_object_get(session, "url", None),
            "currency": currency_code,
            "display_amount": float(converted_total),
        }
    except Exception as exc:
        if exc.__class__.__module__.startswith("stripe"):
            raise HTTPException(status_code=400, detail=str(getattr(exc, "user_message", str(exc))))
        raise HTTPException(status_code=500, detail="Payment service error")


def confirm_card_payment(body: ConfirmCardPaymentRequest, current_user: dict, db: Session) -> dict:
    """
    Confirm card payment synchronously after frontend card confirmation.

    This reduces checkout latency by finalizing the order without waiting for
    asynchronous webhook delivery while remaining idempotent with webhook flow.
    """
    order = _get_user_order(body.order_id, current_user, db)
    if _normalized_payment_method(order) != "card":
        raise HTTPException(status_code=409, detail="This order is not configured for card payment")
    if order.status in INVENTORY_RELEASE_STATUSES:
        raise HTTPException(status_code=409, detail="Order is already closed")

    if body.payment_intent_id and order.payment_intent_id and body.payment_intent_id != order.payment_intent_id:
        raise HTTPException(status_code=409, detail="payment_intent_id does not match this order")

    if order.paid_at is not None:
        return {
            "status": "confirmed",
            "order_id": order.id,
            "order_status": order.status,
            "payment_intent_id": body.payment_intent_id or cast(Optional[str], getattr(order, "payment_intent_id", None)),
            "payment_status": "succeeded",
            "paid_at": order.paid_at,
        }

    if not _stripe_configured(db):
        raise HTTPException(status_code=503, detail="Payment service not configured")
    _apply_stripe_runtime_key(db)

    payment_intent_id = body.payment_intent_id or order.payment_intent_id
    checkout_session_id = (body.checkout_session_id or "").strip()
    if checkout_session_id:
        try:
            session = stripe.checkout.Session.retrieve(checkout_session_id)
        except Exception as exc:
            if exc.__class__.__module__.startswith("stripe"):
                raise HTTPException(status_code=400, detail=str(getattr(exc, "user_message", str(exc))))
            raise HTTPException(status_code=502, detail="Unable to verify checkout session") from exc

        session_client_reference = str(_stripe_object_get(session, "client_reference_id", "") or "").strip()
        if session_client_reference and session_client_reference != str(order.id):
            raise HTTPException(status_code=409, detail="checkout_session_id does not belong to this order")

        session_metadata = _stripe_metadata_map(session)
        if session_metadata.get("order_id") and session_metadata.get("order_id") != str(order.id):
            raise HTTPException(status_code=409, detail="checkout_session_id does not belong to this order")

        session_payment_intent = _stripe_object_get(session, "payment_intent", None)
        if isinstance(session_payment_intent, dict):
            payment_intent_id = str(_stripe_object_get(session_payment_intent, "id", "") or "").strip() or payment_intent_id
        else:
            payment_intent_id = str(session_payment_intent or payment_intent_id or "").strip() or None

    if not payment_intent_id:
        raise HTTPException(status_code=422, detail="payment_intent_id is required")

    try:
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)
    except Exception as exc:
        if exc.__class__.__module__.startswith("stripe"):
            raise HTTPException(status_code=400, detail=str(getattr(exc, "user_message", str(exc))))
        raise HTTPException(status_code=502, detail="Unable to verify payment intent") from exc

    strict_metadata_match = not bool(order.payment_intent_id)
    valid_intent, validation_reason = _payment_intent_matches_order(
        intent,
        order=order,
        expected_user_id=int(current_user["id"]),
        require_metadata=strict_metadata_match,
    )
    if not valid_intent:
        logger.warning(
            "Stripe confirmation rejected for order=%s payment_intent=%s reason=%s",
            order.id,
            payment_intent_id,
            validation_reason,
        )
        raise HTTPException(status_code=409, detail="payment_intent_id does not belong to this order")

    if getattr(order, "payment_intent_id", None) != payment_intent_id:
        setattr(order, "payment_intent_id", payment_intent_id)

    intent_status = _payment_intent_status(intent)

    if intent_status == "succeeded":
        _apply_successful_payment(
            order,
            f"Order #{order.id} payment was successful. We are preparing your order.",
            db,
        )
        db.commit()
        return {
            "status": "confirmed",
            "order_id": order.id,
            "order_status": order.status,
            "payment_intent_id": payment_intent_id,
            "payment_status": intent_status,
            "paid_at": order.paid_at,
        }

    if intent_status in {"requires_payment_method", "canceled"}:
        setattr(order, "status", "failed")
        db.commit()
        return {
            "status": "failed",
            "order_id": order.id,
            "order_status": order.status,
            "payment_intent_id": payment_intent_id,
            "payment_status": intent_status,
            "paid_at": order.paid_at,
        }

    return {
        "status": "pending_verification",
        "order_id": order.id,
        "order_status": order.status,
        "payment_intent_id": payment_intent_id,
        "payment_status": intent_status or "pending",
        "paid_at": order.paid_at,
    }


# ── Stripe webhook ────────────────────────────────────────────────────────────

async def handle_stripe_webhook(request: Request, db: Session) -> dict:
    webhook_secret = _resolve_stripe_webhook_secret(db)
    if not webhook_secret:
        raise HTTPException(status_code=503, detail="Webhook secret not configured")
    _apply_stripe_runtime_key(db)

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing stripe-signature header")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except Exception as exc:
        if exc.__class__.__name__ == "SignatureVerificationError":
            raise HTTPException(status_code=400, detail="Invalid signature")
        raise

    event_type = event["type"]
    obj = event["data"]["object"]
    stripe_event_id = event.get("id", "")

    # ── Idempotency: skip events we have already processed ────────────────────
    if stripe_event_id:
        already_processed = db.query(ProcessedWebhookEvent).filter(
            ProcessedWebhookEvent.event_id == stripe_event_id,
            ProcessedWebhookEvent.processor == "stripe",
        ).first()
        if already_processed:
            logger.info("Stripe webhook duplicate ignored: event_id=%s", stripe_event_id)
            return {"status": "ok"}

    if event_type == "payment_intent.succeeded":
        pi_id = _payment_intent_id(obj)
        metadata = _stripe_metadata_map(obj)
        metadata_order_id = metadata.get("order_id")
        order = db.query(Order).filter(Order.payment_intent_id == pi_id).first()
        if not order and metadata_order_id and metadata_order_id.isdigit():
            order = db.query(Order).filter(Order.id == int(metadata_order_id)).first()
            if order and not getattr(order, "payment_intent_id", None):
                setattr(order, "payment_intent_id", pi_id)
        if order:
            valid_intent, validation_reason = _payment_intent_matches_order(
                obj,
                order=order,
                expected_user_id=int(cast(int, order.user_id)),
                require_metadata=False,
            )
            if not valid_intent:
                logger.error(
                    "payment_intent.succeeded rejected for order %s pi=%s reason=%s",
                    order.id,
                    pi_id,
                    validation_reason,
                )
            elif order.status in INVENTORY_RELEASE_STATUSES:
                logger.warning(
                    "payment_intent.succeeded ignored for terminal order %s in status %s",
                    order.id,
                    order.status,
                )
            elif order.paid_at is not None:
                logger.info(
                    "payment_intent.succeeded duplicate ignored for already processed order %s status=%s",
                    order.id,
                    order.status,
                )
            else:
                _apply_successful_payment(
                    order,
                    f"Order #{order.id} payment was successful. We are preparing your order.",
                    db,
                )
                db.commit()
                try:
                    from services.transactional_email_service import enqueue_payment_confirmed_email

                    enqueue_payment_confirmed_email(cast(int, order.id), provider="stripe", message="Your Stripe payment was successful and we are preparing your order.")
                except Exception:
                    logger.exception("Failed to enqueue Stripe payment-confirmed email for order %s", order.id)
                logger.info("payment_intent.succeeded: order %s status=%s", order.id, order.status)
        else:
            logger.warning("payment_intent.succeeded: no order for pi=%s", pi_id)

    elif event_type == "payment_intent.payment_failed":
        pi_id = _payment_intent_id(obj)
        metadata = _stripe_metadata_map(obj)
        metadata_order_id = metadata.get("order_id")
        last_error = _stripe_object_get(obj, "last_payment_error", {}) or {}
        error_msg = (
            last_error.get("message", "Payment failed")
            if isinstance(last_error, dict)
            else str(_stripe_object_get(last_error, "message", "Payment failed"))
        )
        order = db.query(Order).filter(Order.payment_intent_id == pi_id).first()
        if not order and metadata_order_id and metadata_order_id.isdigit():
            order = db.query(Order).filter(Order.id == int(metadata_order_id)).first()
            if order and not getattr(order, "payment_intent_id", None):
                setattr(order, "payment_intent_id", pi_id)
        if order:
            valid_intent, validation_reason = _payment_intent_matches_order(
                obj,
                order=order,
                expected_user_id=int(cast(int, order.user_id)),
                require_metadata=False,
            )
            if not valid_intent:
                logger.error(
                    "payment_intent.payment_failed rejected for order %s pi=%s reason=%s",
                    order.id,
                    pi_id,
                    validation_reason,
                )
            elif order.paid_at is not None or order.status in INVENTORY_RELEASE_STATUSES:
                logger.warning(
                    "payment_intent.payment_failed ignored for order %s in status %s paid_at=%s",
                    order.id,
                    order.status,
                    order.paid_at,
                )
            else:
                setattr(order, "status", "failed")
                db.add(
                    Notification(
                        user_id=order.user_id,
                        type="order_update",
                        title="Payment Failed",
                        message=f"Order #{order.id} payment failed: {error_msg}. Please try again.",
                        link=f"/orders/{order.id}",
                    )
                )
                db.commit()
                try:
                    from services.transactional_email_service import enqueue_payment_failed_email

                    enqueue_payment_failed_email(cast(int, order.id), provider="stripe", message=error_msg)
                except Exception:
                    logger.exception("Failed to enqueue Stripe payment-failed email for order %s", order.id)
                logger.info("payment_intent.payment_failed: order %s failed", order.id)

    elif event_type == "charge.refunded":
        pi_id = obj.get("payment_intent")
        if pi_id:
            order = db.query(Order).filter(Order.payment_intent_id == pi_id).first()
            if order:
                restored_inventory = apply_order_status_change(order, "refunded", db)
                try:
                    from services.cash_management_service import log_refund_bank_transaction

                    refund_items = obj.get("refunds", {}).get("data", [])
                    refund_ref = refund_items[0].get("id") if refund_items else None
                    log_refund_bank_transaction(
                        order,
                        db,
                        source="stripe_refund",
                        transaction_ref=refund_ref or f"{pi_id}:refund",
                        description=f"Stripe refund settled for order #{order.id}",
                        transaction_date=datetime.now(timezone.utc).replace(tzinfo=None),
                    )
                except Exception:
                    logger.exception("Failed to log Stripe refund bank transaction for order %s", order.id)
                db.add(
                    Notification(
                        user_id=order.user_id,
                        type="order_update",
                        title="Refund Processed",
                        message=f"Your refund for Order #{order.id} has been processed.",
                        link=f"/orders/{order.id}",
                    )
                )
                db.commit()
                try:
                    from services.transactional_email_service import enqueue_refund_processed_email

                    enqueue_refund_processed_email(cast(int, order.id), source="stripe")
                except Exception:
                    logger.exception("Failed to enqueue Stripe refund email for order %s", order.id)
                logger.info(
                    "charge.refunded: order %s refunded restored_inventory=%s",
                    order.id,
                    restored_inventory,
                )

    else:
        logger.debug("Unhandled Stripe event: %s", event_type)

    # Record event as processed (idempotency guard)
    if stripe_event_id:
        db.add(ProcessedWebhookEvent(event_id=stripe_event_id, processor="stripe"))
        db.commit()

    return {"status": "ok"}


# ── Tap Payments ──────────────────────────────────────────────────────────────

async def create_tap_charge(body: TapChargeRequest, current_user: dict, db: Session) -> dict:
    configured, tap_key = _tap_configured(db)
    if not configured:
        raise HTTPException(status_code=503, detail="Tap Payments not configured")
    if not _payment_provider_mode_allows("tap", db):
        raise HTTPException(status_code=409, detail="Tap payments are currently disabled by admin")

    webhook_url = _resolve_tap_webhook_url(db)
    if not webhook_url:
        raise HTTPException(status_code=503, detail="Tap webhook URL not configured")
    tap_api_base_url = _resolve_tap_api_base_url(db)

    order = _get_user_order(body.order_id, current_user, db)
    if _normalized_payment_method(order) != "tap":
        raise HTTPException(status_code=409, detail="This order is not configured for Tap payment")
    if order.paid_at is not None:
        raise HTTPException(status_code=409, detail="Order is already paid")
    currency_code = _resolved_payment_currency(body.currency, body.country)
    charge_total = _order_charge_total_amount(order)
    converted_total = convert_from_aed(charge_total, currency_code)
    redirect_url = body.success_url.strip() or f"{settings.frontend_url}/checkout?tap_order_id={order.id}"
    preferred_language = str(current_user.get("preferred_language") or "en").lower()
    lang_code = "ar" if preferred_language.startswith("ar") else "en"

    payload = {
        "amount": float(converted_total),
        "currency": currency_code,
        "customer_initiated": True,
        "threeDSecure": True,
        "save_card": False,
        "description": body.description or f"ZOZI Order #{order.id}",
        "customer": _build_tap_customer(order, current_user),
        "order": {"id": str(order.id)},
        "metadata": {
            "order_id": str(order.id),
            "user_id": str(current_user["id"]),
            "payment_method": "tap",
            "shipping_country": str(getattr(order, "shipping_country", "") or ""),
            **_order_gateway_metadata(order),
        },
        "source": {"id": "src_all"},
        "redirect": {"url": redirect_url},
        "post": {"url": webhook_url},
        "reference": {
            "transaction": f"zozi_order_{order.id}",
            "order": str(order.id),
        },
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{tap_api_base_url}/v2/charges",
                headers={
                    "Authorization": f"Bearer {tap_key}",
                    "Content-Type": "application/json",
                    "accept": "application/json",
                    "lang_code": lang_code,
                },
                json=payload,
            )
        data = resp.json()
        if resp.status_code not in (200, 201):
            logger.error("Tap charge creation failed: %s", data)
            errors = data.get("errors", [{}])
            raise HTTPException(
                status_code=400,
                detail=errors[0].get("description", "Tap payment failed") if errors else "Tap payment failed",
            )

        charge_id = data.get("id")
        redirect_url = data.get("transaction", {}).get("url") or data.get("redirect", {}).get("url")
        if charge_id:
            setattr(order, "payment_intent_id", charge_id)
            db.commit()
        return {
            "charge_id": charge_id,
            "redirect_url": redirect_url,
            "status": data.get("status"),
            "currency": currency_code,
            "display_amount": float(converted_total),
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Tap charge error: %s", exc)
        raise HTTPException(status_code=500, detail="Tap payment service error")


def _tap_error_detail(payload: dict[str, Any], default: str) -> str:
    errors = payload.get("errors", []) if isinstance(payload, dict) else []
    if isinstance(errors, list) and errors:
        first_error = errors[0]
        if isinstance(first_error, dict):
            description = first_error.get("description")
            if description:
                return str(description)
    message = payload.get("message") if isinstance(payload, dict) else None
    return str(message or default)


def _finalize_tap_charge_status(order: Order, charge_payload: dict[str, Any], db: Session) -> dict[str, Any]:
    charge_id = str(charge_payload.get("id") or getattr(order, "payment_intent_id", "") or "").strip()
    if charge_id and not getattr(order, "payment_intent_id", None):
        setattr(order, "payment_intent_id", charge_id)

    status = str(charge_payload.get("status", "") or "").upper()

    if status == "CAPTURED":
        if order.status not in INVENTORY_RELEASE_STATUSES and order.paid_at is None:
            _apply_successful_payment(
                order,
                f"Order #{order.id} payment via Tap was successful.",
                db,
            )
            db.commit()
            try:
                from services.transactional_email_service import enqueue_payment_confirmed_email

                enqueue_payment_confirmed_email(cast(int, order.id), provider="tap", message="Your Tap payment was successful and we are preparing your order.")
            except Exception:
                logger.exception("Failed to enqueue Tap payment-confirmed email for order %s", order.id)

        return {
            "status": "confirmed",
            "order_id": order.id,
            "order_status": order.status if order.status not in INVENTORY_RELEASE_STATUSES else order.status,
            "charge_id": charge_id,
            "payment_status": status,
            "paid_at": order.paid_at,
        }

    if status == "FAILED":
        if order.paid_at is None and order.status not in INVENTORY_RELEASE_STATUSES:
            setattr(order, "status", "failed")
            db.add(
                Notification(
                    user_id=order.user_id,
                    type="order_update",
                    title="Payment Failed",
                    message=f"Order #{order.id} Tap payment failed.",
                    link=f"/orders/{order.id}",
                )
            )
            db.commit()
            try:
                from services.transactional_email_service import enqueue_payment_failed_email

                enqueue_payment_failed_email(cast(int, order.id), provider="tap", message="Your Tap payment could not be completed.")
            except Exception:
                logger.exception("Failed to enqueue Tap payment-failed email for order %s", order.id)

        return {
            "status": "failed",
            "order_id": order.id,
            "order_status": order.status,
            "charge_id": charge_id,
            "payment_status": status,
            "paid_at": order.paid_at,
        }

    if status == "REFUNDED":
        if order.status != "refunded":
            apply_order_status_change(order, "refunded", db)
            try:
                from services.cash_management_service import log_refund_bank_transaction

                log_refund_bank_transaction(
                    order,
                    db,
                    source="tap_refund",
                    transaction_ref=f"{charge_id}:REFUNDED",
                    description=f"Tap refund settled for order #{order.id}",
                    transaction_date=datetime.now(timezone.utc).replace(tzinfo=None),
                )
            except Exception:
                logger.exception("Failed to log Tap refund bank transaction for order %s", order.id)
            db.add(
                Notification(
                    user_id=order.user_id,
                    type="order_update",
                    title="Refund Processed",
                    message=f"Your Tap refund for Order #{order.id} has been processed.",
                    link=f"/orders/{order.id}",
                )
            )
            db.commit()
            try:
                from services.transactional_email_service import enqueue_refund_processed_email

                enqueue_refund_processed_email(cast(int, order.id), source="tap")
            except Exception:
                logger.exception("Failed to enqueue Tap refund email for order %s", order.id)

        return {
            "status": "refunded",
            "order_id": order.id,
            "order_status": order.status,
            "charge_id": charge_id,
            "payment_status": status,
            "paid_at": order.paid_at,
        }

    return {
        "status": "pending_verification",
        "order_id": order.id,
        "order_status": order.status,
        "charge_id": charge_id,
        "payment_status": status or "pending",
        "paid_at": order.paid_at,
    }


async def confirm_tap_payment(body: ConfirmTapPaymentRequest, current_user: dict, db: Session) -> dict:
    configured, tap_key = _tap_configured(db)
    if not configured:
        raise HTTPException(status_code=503, detail="Tap Payments not configured")
    tap_api_base_url = _resolve_tap_api_base_url(db)

    order = _get_user_order(body.order_id, current_user, db)
    if _normalized_payment_method(order) != "tap":
        raise HTTPException(status_code=409, detail="This order is not configured for Tap payment")

    charge_id = (body.charge_id or cast(Optional[str], getattr(order, "payment_intent_id", None)) or "").strip()
    if not charge_id:
        raise HTTPException(status_code=422, detail="charge_id is required")

    if order.paid_at is not None:
        return {
            "status": "confirmed",
            "order_id": order.id,
            "order_status": order.status,
            "charge_id": charge_id,
            "payment_status": "CAPTURED",
            "paid_at": order.paid_at,
        }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{tap_api_base_url}/v2/charges/{charge_id}",
                headers={
                    "Authorization": f"Bearer {tap_key}",
                    "accept": "application/json",
                },
            )
        data = resp.json()
        if resp.status_code != 200:
            raise HTTPException(status_code=400, detail=_tap_error_detail(data, "Tap payment verification failed"))
        return _finalize_tap_charge_status(order, data, db)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Tap payment confirmation error: %s", exc)
        raise HTTPException(status_code=500, detail="Tap payment verification error")


async def _query_paytabs_transaction(tran_ref: str | None, cart_id: str | None, db: Session) -> dict[str, Any]:
    configured, server_key, profile_id = _paytabs_configured(db)
    if not configured:
        raise HTTPException(status_code=503, detail="PayTabs is not configured")
    payload: dict[str, Any] = {"profile_id": profile_id}
    if tran_ref:
        payload["tran_ref"] = tran_ref
    if cart_id:
        payload["cart_id"] = cart_id
    if not tran_ref and not cart_id:
        raise HTTPException(status_code=422, detail="tran_ref or cart_id is required")

    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(
            f"{_resolve_paytabs_api_base_url(db)}{DEFAULT_PAYTABS_QUERY_PATH}",
            headers={"authorization": server_key, "content-type": "application/json"},
            json=payload,
        )
    data = response.json()
    if response.status_code not in (200, 201):
        raise HTTPException(status_code=400, detail=_paytabs_response_message(data))
    return data


def _finalize_paytabs_transaction(order: Order, payload: dict[str, Any], db: Session) -> dict[str, Any]:
    tran_ref = _paytabs_transaction_reference(payload) or str(getattr(order, "payment_intent_id", "") or "").strip()
    if tran_ref and not getattr(order, "payment_intent_id", None):
        setattr(order, "payment_intent_id", tran_ref)

    response_status = _paytabs_response_status(payload)

    if response_status in PAYTABS_SUCCESS_RESPONSE_STATUSES:
        if order.status not in INVENTORY_RELEASE_STATUSES and order.paid_at is None:
            _apply_successful_payment(order, f"Order #{order.id} payment via PayTabs was successful.", db)
            db.commit()
            try:
                from services.transactional_email_service import enqueue_payment_confirmed_email

                enqueue_payment_confirmed_email(cast(int, order.id), provider="paytabs", message="Your PayTabs payment was successful and we are preparing your order.")
            except Exception:
                logger.exception("Failed to enqueue PayTabs payment-confirmed email for order %s", order.id)

        return {
            "status": "confirmed",
            "order_id": order.id,
            "order_status": order.status,
            "tran_ref": tran_ref,
            "payment_status": response_status,
            "paid_at": order.paid_at,
        }

    if response_status in PAYTABS_FAILURE_RESPONSE_STATUSES:
        if order.paid_at is None and order.status not in INVENTORY_RELEASE_STATUSES:
            setattr(order, "status", "failed")
            db.add(
                Notification(
                    user_id=order.user_id,
                    type="order_update",
                    title="Payment Failed",
                    message=f"Order #{order.id} PayTabs payment failed.",
                    link=f"/orders/{order.id}",
                )
            )
            db.commit()
            try:
                from services.transactional_email_service import enqueue_payment_failed_email

                enqueue_payment_failed_email(cast(int, order.id), provider="paytabs", message=_paytabs_response_message(payload))
            except Exception:
                logger.exception("Failed to enqueue PayTabs payment-failed email for order %s", order.id)

        return {
            "status": "failed",
            "order_id": order.id,
            "order_status": order.status,
            "tran_ref": tran_ref,
            "payment_status": response_status,
            "paid_at": order.paid_at,
        }

    return {
        "status": "pending_verification",
        "order_id": order.id,
        "order_status": order.status,
        "tran_ref": tran_ref,
        "payment_status": response_status or "pending",
        "paid_at": order.paid_at,
    }


async def create_paytabs_charge(body: PayTabsChargeRequest, current_user: dict, db: Session) -> dict:
    configured, server_key, profile_id = _paytabs_configured(db)
    if not configured:
        raise HTTPException(status_code=503, detail="PayTabs is not configured")
    if not _payment_provider_mode_allows(PAYTABS_PAYMENT_METHOD, db):
        raise HTTPException(status_code=409, detail="PayTabs payments are currently disabled by admin")

    callback_url = _resolve_paytabs_callback_url(db)
    if not callback_url:
        raise HTTPException(status_code=503, detail="PayTabs callback URL not configured")

    order = _get_user_order(body.order_id, current_user, db)
    if _normalized_payment_method(order) != PAYTABS_PAYMENT_METHOD:
        raise HTTPException(status_code=409, detail="This order is not configured for PayTabs payment")
    if order.paid_at is not None:
        raise HTTPException(status_code=409, detail="Order is already paid")

    currency_code = _resolved_payment_currency(body.currency, body.country)
    charge_total = _order_charge_total_amount(order)
    converted_total = convert_from_aed(charge_total, currency_code)
    redirect_url = body.success_url.strip() or f"{settings.frontend_url}/checkout?paytabs_order_id={order.id}"
    preferred_language = str(current_user.get("preferred_language") or "en").lower()
    payload = {
        "profile_id": int(profile_id) if str(profile_id).isdigit() else profile_id,
        "tran_type": "sale",
        "tran_class": "ecom",
        "cart_id": str(order.id),
        "cart_currency": currency_code,
        "cart_amount": float(converted_total),
        "cart_description": body.description or f"ZOZI Order #{order.id}",
        "paypage_lang": "ar" if preferred_language.startswith("ar") else "en",
        "customer_details": _paytabs_customer_details(order, current_user),
        "shipping_details": _paytabs_shipping_details(order, current_user),
        "callback": callback_url,
        "return": redirect_url,
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                f"{_resolve_paytabs_api_base_url(db)}{DEFAULT_PAYTABS_REQUEST_PATH}",
                headers={"authorization": server_key, "content-type": "application/json"},
                json=payload,
            )
        data = response.json()
        if response.status_code not in (200, 201):
            raise HTTPException(status_code=400, detail=_paytabs_response_message(data))

        tran_ref = _paytabs_transaction_reference(data)
        if tran_ref:
            setattr(order, "payment_intent_id", tran_ref)
            db.commit()

        return {
            "transaction_reference": tran_ref or None,
            "redirect_url": data.get("redirect_url"),
            "status": _paytabs_response_status(data) or "initiated",
            "currency": currency_code,
            "display_amount": float(converted_total),
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("PayTabs charge error: %s", exc)
        raise HTTPException(status_code=500, detail="PayTabs payment service error")


async def confirm_paytabs_payment(body: ConfirmPayTabsPaymentRequest, current_user: dict, db: Session) -> dict:
    order = _get_user_order(body.order_id, current_user, db)
    if _normalized_payment_method(order) != PAYTABS_PAYMENT_METHOD:
        raise HTTPException(status_code=409, detail="This order is not configured for PayTabs payment")

    if order.paid_at is not None:
        return {
            "status": "confirmed",
            "order_id": order.id,
            "order_status": order.status,
            "tran_ref": str(getattr(order, "payment_intent_id", "") or "").strip() or body.tran_ref,
            "payment_status": "approved",
            "paid_at": order.paid_at,
        }

    payload = await _query_paytabs_transaction(body.tran_ref or cast(Optional[str], getattr(order, "payment_intent_id", None)), str(order.id), db)
    return _finalize_paytabs_transaction(order, payload, db)


def _verify_tap_signature(raw_body: bytes, sig_header: str, db: Session | None = None) -> bool:
    """
    Verify an incoming Tap webhook request.

    Tap signs each webhook POST with an HMAC-SHA256 digest calculated over the
    raw request body, using TAP_WEBHOOK_SECRET as the key.  The digest is
    delivered in the 'hashstring' header (Tap docs, 2024 API reference).

    Returns True when the signature is valid, False otherwise.
    If TAP_WEBHOOK_SECRET is not configured the function returns False so that
    the caller can reject the request with an appropriate HTTP error.
    """
    secret = _resolve_tap_webhook_secret(db)
    if not secret:
        return False
    expected = hmac.new(
        secret.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, sig_header)


async def handle_tap_webhook(request: Request, db: Session) -> dict:
    raw_body = await request.body()

    # ── Signature verification ────────────────────────────────────────────────
    tap_webhook_secret = _resolve_tap_webhook_secret(db)
    if tap_webhook_secret:
        sig_header = request.headers.get("hashstring", "")
        if not sig_header or not _verify_tap_signature(raw_body, sig_header, db):
            logger.warning("tap_webhook: invalid or missing signature")
            raise HTTPException(status_code=400, detail="Invalid Tap webhook signature")
    else:
        # Secret not configured — log a warning but do NOT silently accept.
        # In production, TAP_WEBHOOK_SECRET must be set.
        logger.warning(
            "tap_webhook: TAP_WEBHOOK_SECRET is not configured; "
            "signature verification is skipped. Set TAP_WEBHOOK_SECRET in production."
        )

    try:
        import json
        data = json.loads(raw_body)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    charge_id = data.get("id")
    status = data.get("status", "").upper()

    if not charge_id:
        return {"status": "ignored"}

    # ── Idempotency: skip events we have already processed ────────────────────
    # Tap does not supply a unique event ID separate from the charge ID, so we
    # use "{charge_id}:{status}" as the composite idempotency key.
    tap_event_id = f"{charge_id}:{status}"
    already_processed = db.query(ProcessedWebhookEvent).filter(
        ProcessedWebhookEvent.event_id == tap_event_id,
        ProcessedWebhookEvent.processor == "tap",
    ).first()
    if already_processed:
        logger.info("tap_webhook duplicate ignored: event_id=%s", tap_event_id)
        return {"status": "ok"}

    order = db.query(Order).filter(Order.payment_intent_id == charge_id).first()
    if not order:
        logger.warning("tap_webhook: no order for charge %s", charge_id)
        return {"status": "unknown_order"}
    _finalize_tap_charge_status(order, data, db)

    # Record event as processed (idempotency guard)
    db.add(ProcessedWebhookEvent(event_id=tap_event_id, processor="tap"))
    db.commit()
    logger.info("tap_webhook: charge %s order %s status=%s", charge_id, order.id, status)
    return {"status": "ok"}


async def handle_paytabs_callback(request: Request, db: Session) -> dict:
    raw_body = await request.body()
    signature = request.headers.get("X-PAYTABS-SIGNATURE", "")
    webhook_secret = _resolve_paytabs_webhook_secret(db)
    
    if webhook_secret and not _verify_paytabs_signature(raw_body, signature, webhook_secret):
        logger.warning("paytabs_callback: invalid signature")
        raise HTTPException(status_code=401, detail="Invalid webhook signature")
    
    payload: dict[str, Any] = {}

    if raw_body:
        try:
            payload = json.loads(raw_body)
        except Exception:
            try:
                parsed = parse_qs(raw_body.decode("utf-8"), keep_blank_values=True)
                payload = {key: values[-1] for key, values in parsed.items() if values}
            except Exception:
                payload = {}

    for key, value in request.query_params.items():
        if key not in payload:
            payload[key] = value

    tran_ref = _paytabs_transaction_reference(payload)
    cart_id = str(payload.get("cart_id") or "").strip()
    if not tran_ref and not cart_id:
        return {"status": "ignored"}

    order = None
    if cart_id.isdigit():
        order = db.query(Order).filter(Order.id == int(cart_id)).first()
    if order is None and tran_ref:
        order = db.query(Order).filter(Order.payment_intent_id == tran_ref).first()
    if order is None:
        logger.warning("paytabs_callback: no order for tran_ref=%s cart_id=%s", tran_ref, cart_id)
        return {"status": "unknown_order"}

    queried = await _query_paytabs_transaction(tran_ref or None, cart_id or str(order.id), db)
    response_status = _paytabs_response_status(queried) or "pending"
    paytabs_event_id = f"{_paytabs_transaction_reference(queried) or tran_ref or cart_id}:{response_status}"
    already_processed = db.query(ProcessedWebhookEvent).filter(
        ProcessedWebhookEvent.event_id == paytabs_event_id,
        ProcessedWebhookEvent.processor == PAYTABS_PAYMENT_METHOD,
    ).first()
    if already_processed:
        logger.info("paytabs_callback duplicate ignored: event_id=%s", paytabs_event_id)
        return {"status": "ok"}

    _finalize_paytabs_transaction(order, queried, db)
    db.add(ProcessedWebhookEvent(event_id=paytabs_event_id, processor=PAYTABS_PAYMENT_METHOD))
    db.commit()
    logger.info("paytabs_callback: tran_ref=%s order=%s status=%s", _paytabs_transaction_reference(queried) or tran_ref, order.id, response_status)
    return {"status": "ok"}


# ── PayPal Payments ───────────────────────────────────────────────────────────

async def create_paypal_order(body: PayPalOrderRequest, current_user: dict, db: Session) -> dict:
    """Create a PayPal Orders API v2 order and return the approval URL."""
    configured, client_id, secret, base_url = _paypal_configured(db)
    if not configured:
        raise HTTPException(status_code=503, detail="PayPal not configured")
    if not _paypal_gateway_enabled(db):
        raise HTTPException(status_code=409, detail="PayPal payments are currently disabled")

    order = _get_user_order(body.order_id, current_user, db)
    if _normalized_payment_method(order) != "paypal":
        raise HTTPException(status_code=409, detail="This order is not configured for PayPal payment")
    if order.paid_at is not None:
        raise HTTPException(status_code=409, detail="Order is already paid")

    currency_code = _resolved_payment_currency(body.currency, body.country)
    charge_total = _order_charge_total_amount(order)
    converted_total = convert_from_aed(charge_total, currency_code)

    try:
        access_token = await _paypal_get_access_token(cast(str, client_id), cast(str, secret), base_url)

        payload = {
            "intent": "CAPTURE",
            "purchase_units": [
                {
                    "reference_id": str(order.id),
                    "custom_id": str(order.id),
                    "description": body.description or f"ZOZI Order #{order.id}",
                    "amount": {
                        "currency_code": currency_code,
                        "value": f"{converted_total:.2f}",
                    },
                }
            ],
            "application_context": {
                "brand_name": "ZOZI",
                "landing_page": "LOGIN",
                "user_action": "PAY_NOW",
                "return_url": body.return_url,
                "cancel_url": body.cancel_url,
            },
        }

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{base_url}/v2/checkout/orders",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                    "Prefer": "return=representation",
                },
                json=payload,
            )
        data = resp.json()
        if resp.status_code not in (200, 201):
            logger.error("PayPal order creation failed (%s): %s", resp.status_code, data)
            raise HTTPException(
                status_code=400,
                detail=str(data.get("message") or "PayPal order creation failed"),
            )

        paypal_order_id = data.get("id")
        approve_url = next(
            (link["href"] for link in data.get("links", []) if link.get("rel") == "approve"),
            None,
        )
        if paypal_order_id:
            setattr(order, "payment_intent_id", paypal_order_id)
            db.commit()

        return {
            "paypal_order_id": paypal_order_id,
            "approve_url": approve_url,
            "status": data.get("status"),
            "currency": currency_code,
            "display_amount": float(converted_total),
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("PayPal order creation error: %s", exc)
        raise HTTPException(status_code=500, detail="PayPal payment service error")


async def capture_paypal_order(body: PayPalCaptureRequest, current_user: dict, db: Session) -> dict:
    """Capture an approved PayPal order (called after the customer approves on PayPal)."""
    configured, client_id, secret, base_url = _paypal_configured(db)
    if not configured:
        raise HTTPException(status_code=503, detail="PayPal not configured")

    order = _get_user_order(body.order_id, current_user, db)
    if order.paid_at is not None:
        raise HTTPException(status_code=409, detail="Order is already paid")

    try:
        access_token = await _paypal_get_access_token(cast(str, client_id), cast(str, secret), base_url)

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{base_url}/v2/checkout/orders/{body.paypal_order_id}/capture",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                json={},
            )
        data = resp.json()
        capture_status = str(data.get("status", "") or "").upper()

        if resp.status_code in (200, 201) and capture_status == "COMPLETED":
            capture_units = data.get("purchase_units", [])
            capture_id = None
            if capture_units:
                captures = capture_units[0].get("payments", {}).get("captures", [])
                if captures:
                    capture_id = captures[0].get("id")

            _apply_successful_payment(
                order,
                f"Order #{order.id} payment via PayPal was successful.",
                db,
            )
            if capture_id:
                setattr(order, "payment_intent_id", capture_id)
            db.commit()
            try:
                from services.transactional_email_service import enqueue_payment_confirmed_email

                enqueue_payment_confirmed_email(
                    cast(int, order.id),
                    provider="paypal",
                    message="Your PayPal payment was successful and we are preparing your order.",
                )
            except Exception:
                logger.exception("Failed to enqueue PayPal payment-confirmed email for order %s", order.id)

            return {
                "status": "confirmed",
                "order_id": order.id,
                "order_status": order.status,
                "capture_id": capture_id,
                "paypal_order_id": body.paypal_order_id,
                "paid_at": order.paid_at,
            }

        if capture_status in ("VOIDED", "DECLINED"):
            if order.paid_at is None and order.status not in INVENTORY_RELEASE_STATUSES:
                setattr(order, "status", "failed")
                db.add(
                    Notification(
                        user_id=order.user_id,
                        type="order_update",
                        title="Payment Failed",
                        message=f"Order #{order.id} PayPal payment failed.",
                        link=f"/orders/{order.id}",
                    )
                )
                db.commit()
            return {
                "status": "failed",
                "order_id": order.id,
                "order_status": order.status,
                "paypal_order_id": body.paypal_order_id,
                "paid_at": order.paid_at,
            }

        return {
            "status": "pending",
            "order_id": order.id,
            "order_status": order.status,
            "paypal_order_id": body.paypal_order_id,
            "capture_status": capture_status,
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("PayPal capture error: %s", exc)
        raise HTTPException(status_code=500, detail="PayPal payment service error")


async def handle_paypal_webhook(request: Request, db: Session) -> dict:
    """Verify and process PayPal webhook event notifications."""
    import json as _json

    body_bytes = await request.body()
    try:
        event_data = _json.loads(body_bytes)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid PayPal webhook payload")

    event_id = str(event_data.get("id") or "").strip()
    if event_id:
        existing = db.query(ProcessedWebhookEvent).filter(
            ProcessedWebhookEvent.event_id == event_id,
            ProcessedWebhookEvent.processor == "paypal",
        ).first()
        if existing:
            return {"status": "duplicate"}

    # Verify signature if webhook_id (stored as webhook_secret) is configured
    configured, client_id, secret, base_url = _paypal_configured(db)
    if configured:
        gw_record = _get_gateway_connection_record(db, "paypal")
        webhook_id = decrypt_secret(cast(str | None, getattr(gw_record, "webhook_secret", None))) if gw_record else None
        if client_id and secret and webhook_id:
            try:
                access_token = await _paypal_get_access_token(cast(str, client_id), cast(str, secret), base_url)
                verify_payload = {
                    "auth_algo": request.headers.get("paypal-auth-algo", ""),
                    "cert_url": request.headers.get("paypal-cert-url", ""),
                    "transmission_id": request.headers.get("paypal-transmission-id", ""),
                    "transmission_sig": request.headers.get("paypal-transmission-sig", ""),
                    "transmission_time": request.headers.get("paypal-transmission-time", ""),
                    "webhook_id": webhook_id,
                    "webhook_event": event_data,
                }
                async with httpx.AsyncClient(timeout=10) as http_client:
                    verify_resp = await http_client.post(
                        f"{base_url}/v1/notifications/verify-webhook-signature",
                        headers={
                            "Authorization": f"Bearer {access_token}",
                            "Content-Type": "application/json",
                        },
                        json=verify_payload,
                    )
                if verify_resp.json().get("verification_status") != "SUCCESS":
                    logger.warning("PayPal webhook signature failed: %s", verify_resp.text[:200])
                    raise HTTPException(status_code=400, detail="PayPal webhook signature invalid")
            except HTTPException:
                raise
            except Exception:
                logger.exception("PayPal webhook verification error")

    event_type = str(event_data.get("event_type", "") or "")
    resource = event_data.get("resource", {}) if isinstance(event_data.get("resource"), dict) else {}

    if event_type == "PAYMENT.CAPTURE.COMPLETED":
        capture_id = str(resource.get("id") or "").strip()
        # PayPal puts the custom_id (our order ID) on the purchase unit or resource
        custom_id = str(resource.get("custom_id") or "").strip()
        supplementary = resource.get("supplementary_data") or {}
        pp_order_id = (supplementary.get("related_ids") or {}).get("order_id", "")
        order_ref = custom_id or pp_order_id
        if order_ref and order_ref.isdigit():
            order = db.query(Order).filter(Order.id == int(order_ref)).first()
            if order and order.paid_at is None and order.status not in INVENTORY_RELEASE_STATUSES:
                if capture_id:
                    setattr(order, "payment_intent_id", capture_id)
                _apply_successful_payment(
                    order,
                    f"Order #{order.id} PayPal webhook: payment captured.",
                    db,
                )
                db.commit()
                try:
                    from services.transactional_email_service import enqueue_payment_confirmed_email

                    enqueue_payment_confirmed_email(cast(int, order.id), provider="paypal")
                except Exception:
                    logger.exception("PayPal webhook: failed to enqueue payment email for order %s", order.id)

    elif event_type in ("PAYMENT.CAPTURE.DENIED", "PAYMENT.CAPTURE.DECLINED"):
        custom_id = str(resource.get("custom_id") or "").strip()
        if custom_id and custom_id.isdigit():
            order = db.query(Order).filter(Order.id == int(custom_id)).first()
            if order and order.paid_at is None and order.status not in INVENTORY_RELEASE_STATUSES:
                setattr(order, "status", "failed")
                db.add(
                    Notification(
                        user_id=order.user_id,
                        type="order_update",
                        title="Payment Failed",
                        message=f"Order #{order.id} PayPal payment failed.",
                        link=f"/orders/{order.id}",
                    )
                )
                db.commit()

    elif event_type == "PAYMENT.CAPTURE.REFUNDED":
        # PayPal includes the original capture ID in resource links
        capture_id = ""
        for link in resource.get("links", []):
            if isinstance(link, dict) and link.get("rel") == "up":
                capture_id = str(link.get("href", "")).rsplit("/", 2)[-2]
                break
        if not capture_id:
            capture_id = str(resource.get("custom_id") or "").strip()
        order = db.query(Order).filter(Order.payment_intent_id == capture_id).first() if capture_id else None
        if order and order.status != "refunded":
            apply_order_status_change(order, "refunded", db)
            try:
                from services.cash_management_service import log_refund_bank_transaction

                log_refund_bank_transaction(
                    order,
                    db,
                    source="paypal_refund",
                    transaction_ref=str(resource.get("id") or f"paypal:refund:{order.id}"),
                    description=f"PayPal refund settled for order #{order.id}",
                    transaction_date=datetime.now(timezone.utc).replace(tzinfo=None),
                )
            except Exception:
                logger.exception("Failed to log PayPal refund bank transaction for order %s", order.id)
            db.add(
                Notification(
                    user_id=order.user_id,
                    type="order_update",
                    title="Refund Processed",
                    message=f"Your PayPal refund for Order #{order.id} has been processed.",
                    link=f"/orders/{order.id}",
                )
            )
            db.commit()
            try:
                from services.transactional_email_service import enqueue_refund_processed_email

                enqueue_refund_processed_email(cast(int, order.id), source="paypal")
            except Exception:
                logger.exception("Failed to enqueue PayPal refund email for order %s", order.id)

    else:
        logger.debug("Unhandled PayPal webhook event: %s", event_type)

    if event_id:
        db.add(ProcessedWebhookEvent(event_id=event_id, processor="paypal"))
        db.commit()

    return {"status": "ok"}


# ── Thawani Pay ───────────────────────────────────────────────────────────────

async def create_thawani_session(body: ThawaniCheckoutRequest, current_user: dict, db: Session) -> dict:
    """Create a Thawani hosted-checkout session and return the redirect URL."""
    configured, secret_key, publishable_key, api_base_url = _thawani_configured(db)
    if not configured:
        raise HTTPException(status_code=503, detail="Thawani Pay is not configured")
    if not _thawani_checkout_enabled(db):
        raise HTTPException(status_code=409, detail="Thawani Pay is currently disabled")

    order = _get_user_order(body.order_id, current_user, db)
    if _normalized_payment_method(order) != THAWANI_PAYMENT_METHOD:
        raise HTTPException(status_code=409, detail="This order is not configured for Thawani payment")
    if order.paid_at is not None:
        raise HTTPException(status_code=409, detail="Order is already paid")

    # Convert amount to OMR (from base AED) then to baisa (×1000), must be int
    charge_total = _order_charge_total_amount(order)
    omr_amount = convert_from_aed(charge_total, "OMR")
    unit_amount_baisa = max(1, int(round(float(omr_amount) * 1000)))

    is_uat = "uatcheckout" in api_base_url
    pay_base = DEFAULT_THAWANI_UAT_PAY_BASE if is_uat else DEFAULT_THAWANI_LIVE_PAY_BASE

    payload = {
        "client_reference_id": str(order.id),
        "mode": "payment",
        "products": [
            {
                "name": body.description or f"ZOZI Order #{order.id}",
                "unit_amount": unit_amount_baisa,
                "quantity": 1,
            }
        ],
        "success_url": body.success_url,
        "cancel_url": body.cancel_url,
        "metadata": {
            "Customer name": f"{current_user.get('first_name', '')} {current_user.get('last_name', '')}".strip(),
            "order id": str(order.id),
        },
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{api_base_url}/checkout/session",
                headers={
                    "thawani-api-key": secret_key,
                    "Content-Type": "application/json",
                },
                json=payload,
            )
        data = resp.json()
        if resp.status_code not in (200, 201) or not data.get("success"):
            logger.error("Thawani session creation failed (%s): %s", resp.status_code, data)
            raise HTTPException(
                status_code=400,
                detail=str(data.get("description") or "Thawani checkout session creation failed"),
            )

        session_id = str((data.get("data") or {}).get("session_id") or "").strip()
        if not session_id:
            raise HTTPException(status_code=400, detail="Thawani did not return a session_id")

        checkout_url = f"{pay_base}/pay/{session_id}?key={publishable_key}"

        setattr(order, "payment_intent_id", session_id)
        db.commit()

        return {
            "session_id": session_id,
            "checkout_url": checkout_url,
            "currency": "OMR",
            "display_amount": float(omr_amount),
            "unit_amount_baisa": unit_amount_baisa,
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Thawani session creation error: %s", exc)
        raise HTTPException(status_code=500, detail="Thawani payment service error")


async def handle_thawani_webhook(request: Request, db: Session) -> dict:
    """Verify and process Thawani webhook event notifications."""
    import json as _json

    body_bytes = await request.body()
    body_str = body_bytes.decode("utf-8", errors="replace")

    # ── Signature verification ────────────────────────────────────────────────
    thawani_timestamp = request.headers.get("thawani-timestamp", "")
    thawani_signature = request.headers.get("thawani-signature", "")

    webhook_secret = _resolve_thawani_webhook_secret(db)
    if webhook_secret:
        if not thawani_timestamp or not thawani_signature:
            logger.warning("thawani_webhook: missing signature headers")
            raise HTTPException(status_code=400, detail="Missing Thawani webhook signature headers")
        expected_sig = hmac.new(
            webhook_secret.encode("utf-8"),
            f"{body_str}-{thawani_timestamp}".encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(expected_sig, thawani_signature):
            logger.warning("thawani_webhook: invalid signature")
            raise HTTPException(status_code=400, detail="Invalid Thawani webhook signature")
    else:
        logger.warning(
            "thawani_webhook: THAWANI_WEBHOOK_SECRET is not configured; "
            "signature verification is skipped. Set thawani_webhook_secret in production."
        )

    try:
        event_data = _json.loads(body_bytes)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid Thawani webhook payload")

    event_type = str(event_data.get("type") or event_data.get("event_type") or "").strip()
    data = event_data.get("data") or {}
    if not isinstance(data, dict):
        data = {}

    # ── Idempotency key: use invoice or session_id + event type ──────────────
    invoice_id = str(data.get("invoice") or data.get("id") or "").strip()
    session_id_field = str(data.get("session_id") or data.get("checkout_session_id") or "").strip()
    idempotency_key = f"thawani:{event_type}:{invoice_id or session_id_field}"

    if invoice_id or session_id_field:
        existing = db.query(ProcessedWebhookEvent).filter(
            ProcessedWebhookEvent.event_id == idempotency_key,
            ProcessedWebhookEvent.processor == THAWANI_PAYMENT_METHOD,
        ).first()
        if existing:
            return {"status": "duplicate"}

    # ── Resolve order ─────────────────────────────────────────────────────────
    order = None

    # For checkout.* events: client_reference_id is our order ID
    client_ref = str(data.get("client_reference_id") or "").strip()
    if client_ref and client_ref.isdigit():
        order = db.query(Order).filter(Order.id == int(client_ref)).first()

    # For payment.* events: checkout_invoice links back; try payment_intent_id match
    if order is None:
        checkout_invoice = str(data.get("checkout_invoice") or "").strip()
        if checkout_invoice:
            order = db.query(Order).filter(Order.payment_intent_id == checkout_invoice).first()

    # Fallback: match by session_id stored as payment_intent_id
    if order is None and session_id_field:
        order = db.query(Order).filter(Order.payment_intent_id == session_id_field).first()

    # ── Process event ─────────────────────────────────────────────────────────
    if event_type in ("checkout.session.completed", "session.completed"):
        payment_status = str(data.get("payment_status") or "").strip().lower()
        if payment_status == "paid" and order:
            if order.paid_at is None and order.status not in INVENTORY_RELEASE_STATUSES:
                _apply_successful_payment(
                    order,
                    f"Order #{order.id} payment via Thawani Pay was successful.",
                    db,
                )
                db.commit()
            try:
                from services.transactional_email_service import enqueue_payment_confirmed_email

                enqueue_payment_confirmed_email(
                    cast(int, order.id),
                    provider="thawani",
                    message="Your Thawani Pay payment was successful and we are preparing your order.",
                )
            except Exception:
                logger.exception("Failed to enqueue Thawani payment-confirmed email for order %s", order.id if order else "unknown")

    elif event_type in ("payment.succeeded",):
        if order and order.paid_at is None and order.status not in INVENTORY_RELEASE_STATUSES:
            _apply_successful_payment(
                order,
                f"Order #{order.id} Thawani webhook: payment succeeded.",
                db,
            )
            db.commit()
            try:
                from services.transactional_email_service import enqueue_payment_confirmed_email

                enqueue_payment_confirmed_email(cast(int, order.id), provider="thawani")
            except Exception:
                logger.exception("Thawani webhook: failed to enqueue payment email for order %s", order.id)

    elif event_type in ("payment.failed",):
        if order and order.paid_at is None and order.status not in INVENTORY_RELEASE_STATUSES:
            setattr(order, "status", "failed")
            db.add(
                Notification(
                    user_id=order.user_id,
                    type="order_update",
                    title="Payment Failed",
                    message=f"Order #{order.id} Thawani payment failed.",
                    link=f"/orders/{order.id}",
                )
            )
            db.commit()

    else:
        logger.debug("Unhandled Thawani webhook event: %s", event_type)

    if invoice_id or session_id_field:
        db.add(ProcessedWebhookEvent(event_id=idempotency_key, processor=THAWANI_PAYMENT_METHOD))
        db.commit()

    return {"status": "ok"}


class ConfirmThawaniPaymentRequest(BaseModel):
    order_id: int


async def confirm_thawani_payment(body: ConfirmThawaniPaymentRequest, current_user: dict, db: Session) -> dict:
    """Poll Thawani session status after the customer returns from the hosted checkout page.

    Called by the frontend when the customer lands back on our success URL.  The
    function re-queries Thawani's retrieve-session endpoint to get the authoritative
    payment_status and — if the status is 'paid' — applies the successful payment
    (idempotent: safe to call multiple times).

    Returns a dict with keys:
        status  "confirmed" | "pending" | "failed"
        order_id, order_status, session_id, paid_at
    """
    order = _get_user_order(body.order_id, current_user, db)

    # Already confirmed — return immediately
    if order.paid_at is not None:
        return {
            "status": "confirmed",
            "order_id": order.id,
            "order_status": order.status,
            "session_id": str(getattr(order, "payment_intent_id", "") or "").strip(),
            "paid_at": order.paid_at,
        }

    session_id = str(getattr(order, "payment_intent_id", "") or "").strip()
    if not session_id:
        return {
            "status": "pending",
            "order_id": order.id,
            "order_status": order.status,
            "session_id": None,
            "paid_at": None,
        }

    configured, secret_key, _pub_key, api_base_url = _thawani_configured(db)
    if not configured:
        return {
            "status": "pending",
            "order_id": order.id,
            "order_status": order.status,
            "session_id": session_id,
            "paid_at": None,
        }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{api_base_url}/checkout/session/{session_id}",
                headers={"thawani-api-key": secret_key},
            )
        data = resp.json()
        session_data = data.get("data") or {}
        if not isinstance(session_data, dict):
            session_data = {}
        payment_status = str(session_data.get("payment_status") or "").strip().lower()
    except Exception as exc:
        logger.error("Thawani confirm: session retrieve error: %s", exc)
        return {
            "status": "pending",
            "order_id": order.id,
            "order_status": order.status,
            "session_id": session_id,
            "paid_at": None,
        }

    if payment_status == "paid":
        if order.paid_at is None and order.status not in INVENTORY_RELEASE_STATUSES:
            _apply_successful_payment(
                order,
                f"Order #{order.id} Thawani confirm: payment_status=paid.",
                db,
            )
            db.commit()
            try:
                from services.transactional_email_service import enqueue_payment_confirmed_email

                enqueue_payment_confirmed_email(
                    cast(int, order.id),
                    provider="thawani",
                    message="Your Thawani Pay payment was successful and we are preparing your order.",
                )
            except Exception:
                logger.exception("Thawani confirm: failed to enqueue email for order %s", order.id)
        return {
            "status": "confirmed",
            "order_id": order.id,
            "order_status": order.status,
            "session_id": session_id,
            "paid_at": order.paid_at,
        }

    if payment_status in ("cancelled", "failed", "refunded"):
        if order.paid_at is None and order.status not in INVENTORY_RELEASE_STATUSES:
            setattr(order, "status", "failed")
            db.commit()
        return {
            "status": "failed",
            "order_id": order.id,
            "order_status": order.status,
            "session_id": session_id,
            "paid_at": None,
        }

    return {
        "status": "pending",
        "order_id": order.id,
        "order_status": order.status,
        "session_id": session_id,
        "paid_at": None,
    }


# ── Gateway Wizard Controller ───────────────────────────────────────────────────

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
        adapter = PaymentGatewayRegistry.get_or_raise(provider_code)
        adapter_instance = adapter()
        credentials_valid = adapter_instance.validate_credentials({
            "secret_key": payload.secret_key,
            "webhook_secret": payload.webhook_secret,
            "public_key": payload.public_key,
            "merchant_id": payload.merchant_id,
            "api_base_url": payload.api_base_url,
        })
    
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


# ── Universal / generic hosted-redirect gateway adapter ────────────────────────
#
# This adapter makes ANY payment provider plug-and-play. An admin configures a
# gateway connection (provider_kind="custom") with:
#   * api_base_url / webhook_url  — provider endpoints
#   * secret_key / public_key     — credentials
#   * extra_config (JSON) describing how to build the hosted checkout redirect:
#       redirect_url_template : URL with {order_id}{amount}{currency}{reference}
#                               {callback_url}{success_url}{cancel_url}
#                               {customer_email}{customer_name}{description}
#       create_url            : (optional) server-side endpoint to call first to
#                               obtain a hosted-checkout URL (Paymob-style).
#       create_method         : GET|POST (default POST)
#       create_auth_header    : template, e.g. "Bearer {secret_key}"
#       create_body           : {logical_field: actual_field} mapping
#       redirect_url_field    : response JSON key holding the redirect URL
#       redirect_method       : GET|POST (default GET) used when create_url returns
#                               a URL the customer must POST to.
#       order_id_field        : callback JSON/form field holding the order id
#       transaction_ref_field : callback field holding the gateway reference
#       status_field          : callback field holding the status
#       success_values        : list of statuses considered successful
#                               (default ["paid","completed","success","approved",
#                                "captured","a","A","success","done"])
# The storefront redirects the customer to the resulting URL; the provider then
# calls back to /payments/generic/{code}/callback to finalize the order.


class GenericGatewayCreateRequest(BaseModel):
    gateway_code: str
    order_id: Optional[int] = None
    currency: Optional[str] = None
    country: Optional[str] = None
    description: str = "ZOZI Purchase"
    success_url: str = ""
    cancel_url: str = ""

    def model_post_init(self, __context: object) -> None:  # noqa: D401
        if not self.success_url:
            self.success_url = (
                f"{settings.frontend_url}/checkout?generic_order_id={self.order_id}"
                f"&gateway={self.gateway_code}"
            )
        if not self.cancel_url:
            self.cancel_url = (
                f"{settings.frontend_url}/checkout?generic_order_id={self.order_id}"
                f"&gateway={self.gateway_code}&generic_cancelled=true"
            )


class ConfirmGenericGatewayRequest(BaseModel):
    order_id: int
    gateway_code: str
    reference: Optional[str] = None


_GENERIC_DEFAULT_SUCCESS_VALUES = (
    "paid", "completed", "complete", "success", "successful", "approved",
    "captured", "done", "settled", "a", "A", "paid_success",
)


def _resolve_gateway_callback_base(db: Session, provider_code: str) -> str:
    record = _get_gateway_connection_record(db, provider_code)
    configured = _optional_text(getattr(record, "webhook_url", None)) if record else None
    if configured:
        return configured.rstrip("/")
    base = os.getenv("BACKEND_PUBLIC_URL") or getattr(settings, "backend_public_url", "") or getattr(settings, "frontend_url", "")
    return str(base).rstrip("/")


def _fill_gateway_template(template: str, ctx: dict[str, Any]) -> str:
    def repl(match: "re.Match[str]") -> str:
        key = match.group(1)
        value = ctx.get(key, "")
        return str(value if value is not None else "")

    return re.sub(r"\{([a-zA-Z0-9_]+)\}", repl, template)


def _build_generic_redirect(
    gateway: PaymentGatewayConnectionResponse,
    order: Order,
    reference: str,
    currency_code: str,
    converted_total: float,
    db: Session,
) -> dict[str, Any]:
    record = _get_gateway_connection_record(db, gateway.provider_code)
    extra = _json_load_dict(getattr(record, "extra_config_json", None)) if record else {}

    callback_url = f"{_resolve_gateway_callback_base(db, gateway.provider_code)}/payments/generic/{gateway.provider_code}/callback"
    ctx: dict[str, Any] = {
        "order_id": order.id,
        "amount": converted_total,
        "currency": currency_code,
        "reference": reference,
        "callback_url": callback_url,
        "success_url": "",
        "cancel_url": "",
        "customer_email": "",
        "customer_name": "",
        "description": f"ZOZI Order #{order.id}",
    }

    create_url = _optional_text(extra.get("create_url"))
    if create_url:
        create_method = str(extra.get("create_method", "POST")).upper()
        auth_header_tpl = _optional_text(extra.get("create_auth_header"))
        headers: dict[str, str] = {"content-type": "application/json", "accept": "application/json"}
        if auth_header_tpl:
            headers["Authorization"] = _fill_gateway_template(auth_header_tpl, {**ctx, "secret_key": _optional_text(getattr(record, "secret_key", None)) or ""})
        body_fields = extra.get("create_body") or {}
        body: dict[str, Any] = {}
        for logical, actual in body_fields.items():
            body[actual] = ctx.get(logical)
        body["order_id"] = order.id
        body["amount"] = converted_total
        body["currency"] = currency_code
        body["customer_email"] = getattr(order, "customer_email", None) or ctx["customer_email"]
        body["customer_name"] = getattr(order, "customer_name", None) or ctx["customer_name"]
        body["reference"] = reference
        body["callback_url"] = callback_url
        body["return_url"] = ctx["success_url"] or f"{settings.frontend_url}/checkout?generic_order_id={order.id}&gateway={gateway.provider_code}"
        try:
            with httpx.Client(timeout=20) as client:
                resp = client.request(create_method, create_url, headers=headers, json=body)
                if resp.status_code >= 400:
                    raise HTTPException(status_code=502, detail=f"Gateway '{gateway.provider_code}' create call failed ({resp.status_code})")
                data = resp.json()
        except HTTPException:
            raise
        except Exception as exc:
            logger.error("generic gateway create call error: %s", exc)
            raise HTTPException(status_code=502, detail="Gateway connection error")
        redirect_url = _optional_text(data.get(str(extra.get("redirect_url_field", "redirect_url"))))
        redirect_method = str(extra.get("redirect_method", "GET")).upper()
        if not redirect_url:
            raise HTTPException(status_code=502, detail="Gateway did not return a redirect URL")
        return {"redirect_url": redirect_url, "redirect_method": redirect_method, "reference": reference}

    template = _optional_text(extra.get("redirect_url_template")) or _optional_text(gateway.api_base_url)
    if not template:
        raise HTTPException(status_code=503, detail="Gateway redirect URL is not configured")
    return {"redirect_url": _fill_gateway_template(template, ctx), "redirect_method": "GET", "reference": reference}


def create_generic_gateway_payment(body: GenericGatewayCreateRequest, current_user: dict, db: Session) -> dict:
    """Initiate a hosted-redirect payment for any configured gateway."""
    normalized_code = _normalize_gateway_code(body.gateway_code)
    order = _get_user_order(body.order_id, current_user, db)
    if order.paid_at is not None:
        raise HTTPException(status_code=409, detail="Order is already paid")
    if order.status in INVENTORY_RELEASE_STATUSES:
        raise HTTPException(status_code=409, detail="Order is already closed")

    order_country = str(getattr(order, "shipping_country", "") or body.country or "") or None
    record = _get_gateway_connection_record(db, normalized_code, order_country)
    if record is None:
        raise HTTPException(status_code=404, detail="Gateway not found")
    if not getattr(record, "is_enabled", False) or not getattr(record, "supports_customer_checkout", False):
        raise HTTPException(status_code=409, detail="This gateway is not enabled for customer checkout")

    currency_code = _resolved_payment_currency(body.currency, body.country)
    charge_total = _order_charge_total_amount(order)
    converted_total = convert_from_aed(charge_total, currency_code)

    reference = f"gen_{order.id}_{uuid.uuid4().hex[:12]}"
    setattr(order, "payment_intent_id", reference)
    setattr(order, "payment_method", normalized_code)

    gateway = _serialize_gateway_connection(normalized_code, db, record)
    redirect = _build_generic_redirect(gateway, order, reference, currency_code, float(converted_total), db)

    db.add(Payment(
        order_id=order.id,
        amount=charge_total,
        payment_method=normalized_code,
        provider=normalized_code,
        status="pending",
        intent_id=reference,
        country_code=str(getattr(order, "shipping_country", "") or body.country or "") or None,
    ))
    db.commit()

    return {
        "gateway_code": normalized_code,
        "reference": reference,
        "redirect_url": redirect["redirect_url"],
        "redirect_method": redirect["redirect_method"],
        "currency": currency_code,
        "display_amount": float(converted_total),
        "status": "initiated",
    }


def _parse_generic_payload(raw_body: bytes, query_params) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    if raw_body:
        try:
            payload = json.loads(raw_body)
        except Exception:
            try:
                parsed = parse_qs(raw_body.decode("utf-8"), keep_blank_values=True)
                payload = {k: v[-1] for k, v in parsed.items() if v}
            except Exception:
                payload = {}
    for key, value in query_params.items():
        if key not in payload:
            payload[key] = value
    return payload


def _resolve_generic_order(payload: dict[str, Any], provider_code: str, db: Session) -> Optional[Order]:
    order_id_field = str(payload.get("order_id_field", "cart_id") or "cart_id")
    order_id_value = payload.get(order_id_field) or payload.get("order_id") or payload.get("cart_id")
    tran_ref = (
        payload.get("tran_ref")
        or payload.get("reference")
        or payload.get("transaction_ref")
        or payload.get("payment_ref")
    )

    if order_id_value and str(order_id_value).isdigit():
        order = db.query(Order).filter(Order.id == int(order_id_value)).first()
        if order:
            return order
    if tran_ref:
        order = db.query(Order).filter(Order.payment_intent_id == str(tran_ref).strip()).first()
        if order:
            return order
    return None


def _peek_generic_order(provider_code: str, db: Session) -> Optional["Order"]:
    """Best-effort order lookup from the current request body for country resolution.

    Used by the callback handler to pick the correct per-country gateway config
    without duplicating the full payload parsing/resolution done later.
    """
    try:
        raw_body = getattr(_peek_generic_order, "_raw_body", None)
        query_params = getattr(_peek_generic_order, "_query_params", None)
        if raw_body is None:
            return None
        payload = _parse_generic_payload(raw_body, query_params or {})
        return _resolve_generic_order(payload, provider_code, db)
    except Exception:
        return None


async def handle_generic_gateway_callback(request: Request, provider_code: str, db: Session) -> dict:
    normalized_code = _normalize_gateway_code(provider_code)
    # Resolve the gateway connection using the order's country when available so
    # per-country gateway configs are honoured even on server-to-server callbacks.
    _peek_generic_order._raw_body = await request.body()
    _peek_generic_order._query_params = request.query_params
    callback_order = _peek_generic_order(provider_code, db)
    callback_country = str(getattr(callback_order, "shipping_country", "") or "") or None
    record = _get_gateway_connection_record(db, normalized_code, callback_country)
    if record is None:
        raise HTTPException(status_code=404, detail="Gateway not found")

    extra = _json_load_dict(getattr(record, "extra_config_json", None)) if record else {}
    webhook_secret = _optional_text(getattr(record, "webhook_secret", None))
    raw_body = await request.body()
    _payload_hash = hashlib.sha256(raw_body or b"").hexdigest()
    if webhook_secret:
        signature = request.headers.get("X-SIGNATURE") or request.headers.get("X-GATEWAY-SIGNATURE") or ""
        if not _verify_paytabs_signature(raw_body, signature, webhook_secret):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    payload = _parse_generic_payload(raw_body, request.query_params)
    status_field = str(extra.get("status_field", "status") or "status")
    success_values = [str(v).lower() for v in (extra.get("success_values") or list(_GENERIC_DEFAULT_SUCCESS_VALUES))]
    tran_ref_field = str(extra.get("transaction_ref_field", "tran_ref") or "tran_ref")
    order_id_field = str(extra.get("order_id_field", "cart_id") or "cart_id")

    order = _resolve_generic_order(payload, normalized_code, db)
    if order is None:
        logger.warning("generic_callback %s: no order resolved", normalized_code)
        return {"status": "unknown_order"}

    resolved_status = str(payload.get(status_field) or payload.get("response_status") or "").lower()
    tran_ref = payload.get(tran_ref_field) or str(getattr(order, "payment_intent_id", "") or "").strip()
    event_id = f"{normalized_code}:{tran_ref or order.id}:{resolved_status}"
    already = db.query(ProcessedWebhookEvent).filter(
        ProcessedWebhookEvent.event_id == event_id,
        ProcessedWebhookEvent.processor == normalized_code,
    ).first()
    if already:
        return {"status": "ok"}

    success = resolved_status in success_values
    if not resolved_status:
        # No explicit status delivered (e.g. redirect-style return). Treat the
        # callback itself as an authorization to mark the order paid when the
        # gateway is configured without a status field.
        success = True

    if success and order.paid_at is None and order.status not in INVENTORY_RELEASE_STATUSES:
        if tran_ref:
            setattr(order, "payment_intent_id", tran_ref)
        _apply_successful_payment(order, f"Order #{order.id} payment via {normalized_code} was successful.", db)
        db.add(ProcessedWebhookEvent(event_id=event_id, processor=normalized_code, payload_hash=_payload_hash))
        db.commit()
        return {"status": "ok", "order_id": order.id, "result": "confirmed"}

    if not success and order.paid_at is None and order.status not in INVENTORY_RELEASE_STATUSES:
        setattr(order, "status", "failed")
        db.add(ProcessedWebhookEvent(event_id=event_id, processor=normalized_code, payload_hash=_payload_hash))
        db.commit()
        return {"status": "ok", "order_id": order.id, "result": "failed"}

    db.add(ProcessedWebhookEvent(event_id=event_id, processor=normalized_code))
    db.commit()
    return {"status": "ok", "order_id": order.id}


def _generic_verify_payment(
    extra: dict[str, Any],
    record: "PaymentGatewayConnection",
    order: Order,
    reference: str,
    db: Session,
) -> str:
    """Poll a configured provider verify endpoint and return 'success' | 'failed' | 'unknown'."""
    verify_url = _optional_text(extra.get("verify_url"))
    if not verify_url:
        return "unknown"
    normalized_code = _normalize_gateway_code(getattr(record, "provider_code", ""))
    callback_url = f"{_resolve_gateway_callback_base(db, normalized_code)}/payments/generic/{normalized_code}/callback"
    ctx: dict[str, Any] = {
        "order_id": order.id,
        "reference": reference or str(getattr(order, "payment_intent_id", "") or ""),
        "transaction_ref": reference or str(getattr(order, "payment_intent_id", "") or ""),
        "amount": float(_order_charge_total_amount(order)),
        "currency": str(getattr(order, "shipping_country", "") or ""),
        "callback_url": callback_url,
        "customer_email": getattr(order, "customer_email", None) or "",
        "customer_name": getattr(order, "customer_name", None) or "",
    }
    url = _fill_gateway_template(verify_url, ctx)
    method = str(extra.get("verify_method", "GET")).upper()
    headers: dict[str, str] = {"accept": "application/json"}
    auth_header = _optional_text(extra.get("verify_auth_header"))
    if auth_header:
        headers["Authorization"] = _fill_gateway_template(
            auth_header, {**ctx, "secret_key": _optional_text(getattr(record, "secret_key", None)) or ""}
        )
    try:
        with httpx.Client(timeout=20) as client:
            resp = client.request(method, url, headers=headers)
            if resp.status_code >= 400:
                logger.warning("generic verify %s failed: %s", normalized_code, resp.status_code)
                return "unknown"
            data = resp.json()
    except Exception as exc:
        logger.error("generic verify call error: %s", exc)
        return "unknown"

    status_field = str(extra.get("verify_status_field", "status") or "status")
    success_values = [str(v).lower() for v in (extra.get("verify_success_values") or list(_GENERIC_DEFAULT_SUCCESS_VALUES))]
    fail_values = [str(v).lower() for v in (extra.get("verify_failed_values") or ["failed", "declined", "error", "cancelled"])]
    resolved = str(data.get(status_field) or "").lower()
    if resolved in success_values:
        return "success"
    if resolved in fail_values:
        return "failed"
    return "unknown"


def confirm_generic_gateway_payment(body: ConfirmGenericGatewayRequest, current_user: dict, db: Session) -> dict:
    order = _get_user_order(body.order_id, current_user, db)
    if order.paid_at is not None:
        return {"status": "confirmed", "order_id": order.id, "order_status": order.status, "payment_status": "approved", "paid_at": order.paid_at}

    normalized_code = _normalize_gateway_code(body.gateway_code)
    order_country = str(getattr(order, "shipping_country", "") or body.country or "") or None
    record = _get_gateway_connection_record(db, normalized_code, order_country)
    if record is None:
        return {"status": "pending", "order_id": order.id, "order_status": order.status, "payment_status": "pending", "paid_at": order.paid_at}

    extra = _json_load_dict(getattr(record, "extra_config_json", None)) or {}
    reference = body.reference or str(getattr(order, "payment_intent_id", "") or "")

    # Optionally poll the provider for the authoritative payment status before
    # trusting the redirect return. This makes the plug-and-play confirm work
    # even for gateways that do not post a server-side callback.
    verify_result = _generic_verify_payment(extra, record, order, reference, db)
    if verify_result == "success":
        _apply_successful_payment(order, f"Order #{order.id} payment via {normalized_code} was successful.", db)
        db.commit()
        return {"status": "confirmed", "order_id": order.id, "order_status": order.status, "payment_status": "approved", "paid_at": order.paid_at}
    if verify_result == "failed":
        setattr(order, "status", "failed")
        db.commit()
        return {"status": "failed", "order_id": order.id, "order_status": order.status, "payment_status": "declined", "paid_at": order.paid_at}

    # If a prior callback already recorded the payment as completed, finalize.
    payment = db.query(Payment).filter(
        Payment.order_id == order.id,
        Payment.provider == normalized_code,
    ).order_by(Payment.id.desc()).first()
    if payment and payment.status == "completed":
        _apply_successful_payment(order, f"Order #{order.id} payment via {normalized_code} was successful.", db)
        db.commit()
        return {"status": "confirmed", "order_id": order.id, "order_status": order.status, "payment_status": "approved", "paid_at": order.paid_at}

    return {"status": "pending", "order_id": order.id, "order_status": order.status, "payment_status": "pending", "paid_at": order.paid_at}

