"""Payment engine — shared models, config, gateway connection management, and core payment processing."""

from __future__ import annotations
import logging
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy.orm import Session
from domains.finance.models.finance import GatewaySettlementSchedule
from domains.finance.models.finance import BankStatementLine
from domains.finance.models.finance import FinanceAutomationLog
from domains.finance.models.finance import FinanceAuditLog
from domains.orders.models.orders import Order
from domains.finance.models.payments import PaymentGatewayConnection
from infrastructure.database.schemas import JournalEntryCreate, JournalLineInput
from domains.finance.services import general_ledger_service as gl
from infrastructure.utils.datetime_utils import utcnow as _utcnow
﻿"""

Payments Service — Stripe and Tap Payments business logic.



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

from providers.payments.stripe_sdk import stripe

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



from domains.catalog.models.products import Product
from domains.comms.models.communication import Notification
from domains.country.models.countries import CountryConfig
from domains.finance.models.finance import TransactionLedger
from domains.governance.models.admin import PaymentProviderConfig
from domains.governance.models.admin import ProcessedWebhookEvent
from domains.orders.models.orders import Order
from domains.orders.models.orders import OrderItem
from domains.catalog.models.promotions import Coupon
from domains.finance.models.payments import Payment
from domains.finance.models.payments import PaymentGatewayConnection

from infrastructure.messaging.events import PaymentConfirmedEvent

from infrastructure.config import settings

from infrastructure.redis.cache import bump_product_cache_version as _bump_product_cache_version

from kernel.money import convert_from_aed, get_currency_context, money_to_minor_units_for_currency, round_money

from infrastructure.messaging.events import EventPublisher
from infrastructure.utils.cache import get_redis_client
from infrastructure.utils.performance_cache import cache_payment_status, set_payment_status, invalidate_payment_status

_PAYMENT_IDEMPOTENCY_TTL = 86400  # 24 hours


def _check_payment_idempotency_key(idempotency_key: str) -> Optional[dict]:
    """Check if a payment idempotency key was already processed. Returns cached result or None."""
    redis_client = get_redis_client()
    if redis_client is None:
        return None
    try:
        raw = redis_client.get(f"payment:idempotency:{idempotency_key}")
        if raw is None:
            return None
        if isinstance(raw, (bytes, bytearray)):
            raw = raw.decode("utf-8")
        return json.loads(raw)
    except Exception:
        return None


def _store_payment_idempotency_result(idempotency_key: str, result: dict) -> None:
    """Store payment result under an idempotency key with 24h TTL."""
    redis_client = get_redis_client()
    if redis_client is None:
        return
    try:
        redis_client.setex(
            f"payment:idempotency:{idempotency_key}",
            _PAYMENT_IDEMPOTENCY_TTL,
            json.dumps(result, default=str),
        )
    except Exception:
        pass


def check_payment_idempotency(idempotency_key: str) -> Optional[dict]:
    """Public helper: check if a payment idempotency key was already processed."""
    return _check_payment_idempotency_key(idempotency_key)


def store_payment_idempotency(idempotency_key: str, result: dict) -> None:
    """Public helper: store payment result under an idempotency key."""
    _store_payment_idempotency_result(idempotency_key, result)



logger = logging.getLogger(__name__)

from infrastructure.observability.circuit_breaker import (
    CircuitBreakerError,
    get_circuit_breaker,
    get_all_breaker_stats,
)
from infrastructure.observability.retry import RetryExhausted, with_retry
from infrastructure.observability.service_observability import (
    generate_correlation_id,
    get_correlation_id,
    instrument_service,
    log_service_error,
    request_context,
    set_context_user,
)

stripe.api_key = str(getattr(settings, "stripe_secret_key", "") or "").strip()

if str(getattr(settings, "stripe_api_version", "") or "").strip():

    stripe.api_version = str(getattr(settings, "stripe_api_version", "") or "").strip()



LOW_STOCK_THRESHOLD = 5

INVENTORY_RELEASE_STATUSES = {"cancelled", "refunded"}

_stripe_breaker = get_circuit_breaker("stripe", failure_threshold=5, recovery_timeout=30)
_tap_breaker = get_circuit_breaker("tap", failure_threshold=5, recovery_timeout=30)
_paytabs_breaker = get_circuit_breaker("paytabs", failure_threshold=5, recovery_timeout=30)
_thawani_breaker = get_circuit_breaker("thawani", failure_threshold=5, recovery_timeout=30)
_paypal_breaker = get_circuit_breaker("paypal", failure_threshold=5, recovery_timeout=30)

_gateway_call_count = 0
_gateway_error_count = 0


def _safe_stripe_call(func_name: str, order_id: int, func: Callable) -> Any:
    """Execute a Stripe SDK call with circuit breaker and structured error logging."""
    global _gateway_call_count, _gateway_error_count
    _gateway_call_count += 1
    try:
        return func()
    except CircuitBreakerError as e:
        _gateway_error_count += 1
        logger.warning(
            "stripe_circuit_open",
            order_id=order_id,
            function=func_name,
            error=str(e),
            correlation_id=get_correlation_id(),
        )
        raise HTTPException(status_code=503, detail="Payment provider temporarily unavailable. Please retry shortly.") from e
    except Exception as exc:
        _gateway_error_count += 1
        if exc.__class__.__module__.startswith("stripe"):
            logger.warning(
                "stripe_api_error",
                order_id=order_id,
                function=func_name,
                error=str(getattr(exc, "user_message", str(exc))),
                error_type=type(exc).__name__,
                correlation_id=get_correlation_id(),
            )
            raise
        logger.error(
            "stripe_unexpected_error",
            order_id=order_id,
            function=func_name,
            error=str(exc),
            error_type=type(exc).__name__,
            correlation_id=get_correlation_id(),
        )
        raise


def _safe_http_call(
    provider: str,
    breaker: Any,
    order_id: int,
    func: Callable,
) -> Any:
    """Execute an HTTP gateway call with circuit breaker protection."""
    global _gateway_call_count, _gateway_error_count
    _gateway_call_count += 1
    try:
        if breaker.state == "open":
            _gateway_error_count += 1
            logger.warning(
                "circuit_breaker_open",
                provider=provider,
                order_id=order_id,
                correlation_id=get_correlation_id(),
            )
            raise HTTPException(
                status_code=503,
                detail=f"{provider} payment provider temporarily unavailable. Please retry shortly.",
            )
        return func()
    except CircuitBreakerError as e:
        _gateway_error_count += 1
        logger.warning(
            "circuit_breaker_rejected",
            provider=provider,
            order_id=order_id,
            error=str(e),
            correlation_id=get_correlation_id(),
        )
        raise HTTPException(status_code=503, detail=f"{provider} payment provider temporarily unavailable.") from e
    except HTTPException:
        raise
    except Exception as exc:
        _gateway_error_count += 1
        logger.error(
            "gateway_http_error",
            provider=provider,
            order_id=order_id,
            error=str(exc),
            error_type=type(exc).__name__,
            correlation_id=get_correlation_id(),
        )
        raise

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

    idempotency_key: Optional[str] = None





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

    amount: Optional[Decimal] = None

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

    amount: Optional[Decimal] = None

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

    fee_percent: Decimal

    fixed_fee_amount: Decimal

    payout_fee_percent: Decimal

    payout_fixed_fee_amount: Decimal

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

    order_total: Decimal

    gateway_fee_amount: Decimal

    customer_payable_total: Decimal

    processor_net_capture: Decimal

    taxable_product_amount: Decimal

    zozi_commission_amount: Decimal

    supplier_payout_estimate: Decimal

    logistics_payout_estimate: Decimal

    estimated_payout_cost: Decimal

    platform_net_after_gateway_and_payout_costs: Decimal

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





def _round_money_value(value: Any) -> Decimal:

    return round_money(_decimal_from_value(value))





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



def issue_stripe_refund(*, db: Session | None, payment_intent_id: str) -> Any:
    """Create a Stripe refund for a payment intent.

    The controller layer must not touch the Stripe SDK directly (auditor rule
    **V6**); this services-layer helper owns the SDK call and the runtime key
    resolution, returning the refund object to the caller.
    """
    api_key = _apply_stripe_runtime_key(db) or os.getenv("STRIPE_SECRET_KEY", "")
    if not api_key:
        raise HTTPException(status_code=503, detail="Payment service not configured")
    return stripe.Refund.create(payment_intent=payment_intent_id)




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
    # Check cache first
    cache_key_id = hash(f"payment_methods_status:{country_code or 'global'}")
    cached = cache_payment_status(cache_key_id)
    if cached is not None:
        return cached

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



    result = {

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

    # Cache the result
    set_payment_status(cache_key_id, result)

    return result





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

    # Invalidate payment methods cache
    try:
        from infrastructure.utils.performance_cache import invalidate_payment_status as _inv
        _inv(hash("payment_methods_status:global"))
        _inv(hash("payment_methods_status:None"))
    except Exception:
        pass

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

            fee_percent=_decimal_from_value(defaults["fee_percent"]),

            fixed_fee_amount=_decimal_from_value(defaults["fixed_fee_amount"]),

            payout_fee_percent=_decimal_from_value(defaults["payout_fee_percent"]),

            payout_fixed_fee_amount=_decimal_from_value(defaults["payout_fixed_fee_amount"]),

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

        fee_percent=_round_money_value(getattr(record, "fee_percent", defaults["fee_percent"])),

        fixed_fee_amount=_round_money_value(getattr(record, "fixed_fee_amount", defaults["fixed_fee_amount"])),

        payout_fee_percent=_round_money_value(getattr(record, "payout_fee_percent", defaults["payout_fee_percent"])),

        payout_fixed_fee_amount=_round_money_value(getattr(record, "payout_fixed_fee_amount", defaults["payout_fixed_fee_amount"])),

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

        order_total=round_money(order_total),

        gateway_fee_amount=round_money(gateway_fee_amount),

        customer_payable_total=round_money(customer_payable_total),

        processor_net_capture=round_money(processor_net_capture),

        taxable_product_amount=round_money(taxable_product_amount),

        zozi_commission_amount=round_money(zozi_commission_amount),

        supplier_payout_estimate=round_money(supplier_payout_estimate),

        logistics_payout_estimate=round_money(logistics_payout_estimate),

        estimated_payout_cost=round_money(estimated_payout_cost),

        platform_net_after_gateway_and_payout_costs=round_money(platform_net),

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

            from domains.finance.services.treasury.cash_management_service import create_refund_ledger_entry

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

        from domains.finance.services.treasury.cash_management_service import create_ledger_entries_for_order, log_card_payment_received
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





_event_publisher = EventPublisher()

# Public aliases preserved for callers that import these names from this module.
# They were renamed to private counterparts in commit 1e4d2e2 but the importers
# were never updated. These restore the public names without changing behavior.
event_publisher = _event_publisher
order_holds_inventory = _order_holds_inventory





def _apply_successful_payment(order: Order, confirmation_message: str, db: Session) -> None:

    _confirm_order(order, "Payment Confirmed", confirmation_message, db, mark_paid=True)



    total_amount = order.total_amount if order.total_amount is not None else (

        order.subtotal_amount if order.subtotal_amount is not None else 0

    )



    # Post payment journal entry to general ledger

    try:

        from domains.finance.services.ledger.general_ledger_service import post_order_payment_journal

        post_order_payment_journal(db, order.id, total_amount)

    except Exception as e:

        logger.error("Failed to create payment journal entry for order %s: %s", order.id, e)



    # Publish event for async fulfillment processing

    try:

        normalized = _normalized_payment_method(order)

        event = PaymentConfirmedEvent.create(

            payment_id="pending",

            order_id=order.id,

            amount=total_amount,

            currency=order.currency_code or "USD",

            user_id=order.user_id,

            payment_method=normalized,

            payment_gateway=normalized,

        )

        _event_publisher.publish(event)



        db.query(Payment).filter(

            Payment.order_id == order.id,

            Payment.provider == normalized,

        ).update({Payment.status: "completed"})

    except Exception:

        logger.exception("Failed to process PaymentConfirmedEvent for order %s", order.id)





def confirm_cash_on_delivery_order(order: Order, db: Session) -> None:

    _confirm_order(

        order,

        "Order Confirmed",

        f"Order #{order.id} has been placed with Cash on Delivery. We are preparing your order.",

        db,

        mark_paid=False,

    )





# ── Stripe payment intent ─────────────────────────────────────────────────────



