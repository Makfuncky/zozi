"""Shared constants, helpers, and request models for payment gateways.

Relocated from controllers/payments_controller.py during the refactor that moves
the complete payment-gateway connection logic into providers/payments.
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
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from domains.catalog.models.products import Product
from domains.comms.models.communication import Notification
from domains.country.models.countries import CountryConfig
from domains.finance.models.finance import TransactionLedger
from domains.governance.models.admin import PaymentProviderConfig
from domains.governance.models.admin import ProcessedWebhookEvent
from domains.orders.models.orders import Order
from domains.orders.models.orders import OrderItem
from domains.payments.models.payments import Coupon
from domains.payments.models.payments import Payment
from domains.payments.models.payments import PaymentGatewayConnection
from infrastructure.messaging.events import PaymentConfirmedEvent
from infrastructure.utils.config import settings
from infrastructure.utils.currency import (
    convert_from_aed,
    get_currency_context,
    money_to_minor_units_for_currency,
)
from infrastructure.messaging.events import EventPublisher, _event_publisher
import structlog
logger = structlog.get_logger(__name__)

logger = logging.getLogger(__name__)

stripe.api_key = str(getattr(settings, "stripe_secret_key", "") or "").strip()
if str(getattr(settings, "stripe_api_version", "") or "").strip():
    stripe.api_version = str(getattr(settings, "stripe_api_version", "") or "").strip()


__all__ = ['_optional_text', '_normalize_gateway_code', '_normalize_currency_codes', '_decimal_from_value', '_float_money', '_json_load_dict', '_json_load_currency_list', 'normalize_checkout_payment_method', 'gateway_code_for_payment_method', '_normalized_payment_method', 'LOW_STOCK_THRESHOLD', 'INVENTORY_RELEASE_STATUSES', 'INVENTORY_HELD_STATUSES', 'COD_PAYMENT_METHOD', 'PAYTABS_PAYMENT_METHOD', 'THAWANI_PAYMENT_METHOD', 'REUSABLE_STRIPE_INTENT_STATUSES', 'SUPPORTED_CHECKOUT_PAYMENT_METHODS', 'ORDER_PAYMENT_METHOD_GATEWAY_MAP', 'ONLINE_PAYMENT_PROVIDER_MODES', 'SUPPORTED_GATEWAY_KINDS', 'SUPPORTED_GATEWAY_TEST_STATUSES', 'SUPPORTED_SETTLEMENT_CYCLES', 'DEFAULT_SETTLEMENT_CYCLE', 'BUILT_IN_GATEWAY_ORDER', 'BUILT_IN_GATEWAY_CODES', 'LIVE_ADAPTER_GATEWAY_CODES', 'DEFAULT_TAP_API_BASE_URL', 'DEFAULT_TAP_TEST_CHARGE_ID', 'DEFAULT_PAYTABS_API_BASE_URL', 'DEFAULT_PAYPAL_SANDBOX_URL', 'DEFAULT_PAYPAL_LIVE_URL', 'DEFAULT_THAWANI_UAT_URL', 'DEFAULT_THAWANI_LIVE_URL', 'DEFAULT_THAWANI_UAT_PAY_BASE', 'DEFAULT_THAWANI_LIVE_PAY_BASE', 'DEFAULT_PAYTABS_REQUEST_PATH', 'DEFAULT_PAYTABS_QUERY_PATH', 'PAYTABS_SUCCESS_RESPONSE_STATUSES', 'PAYTABS_PENDING_RESPONSE_STATUSES', 'PAYTABS_FAILURE_RESPONSE_STATUSES', 'TAP_COUNTRY_DIAL_CODES', 'PaymentIntentRequest', 'StripeCheckoutSessionRequest', 'ConfirmCardPaymentRequest', 'ConfirmTapPaymentRequest', 'ConfirmPayTabsPaymentRequest', 'TapChargeRequest', 'PayTabsChargeRequest', 'PayPalOrderRequest', 'PayPalCaptureRequest', 'ThawaniCheckoutRequest', 'PaymentMethodsStatus', 'PaymentProviderRuntimeConfigRequest', 'PaymentProviderRuntimeConfigResponse', 'PaymentGatewayConnectionRequest', 'PaymentGatewayConnectionResponse', 'PaymentGatewayTestResponse', 'GatewayWizardRequest', 'GatewayWizardResponse', 'PaymentFinanceQuoteRequest', 'PaymentFinanceQuoteResponse', 'ConfirmThawaniPaymentRequest', 'GenericGatewayCreateRequest', 'ConfirmGenericGatewayRequest', 'GatewayDispatchRequest']


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


class GatewayDispatchRequest(BaseModel):
    """Gateway-agnostic request body for the registry-driven dispatch routes.

    The generic ``/{gateway}/create`` and ``/{gateway}/confirm`` endpoints use
    this permissive model so a newly registered gateway is reachable without
    adding a typed request model or touching the router. Adapters read the
    common fields (``order_id``, ``amount``, ``currency``, ``country``) and may
    consume gateway-specific values from ``extra``.
    """

    order_id: Optional[int] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    country: Optional[str] = None
    reference: Optional[str] = None
    extra: dict[str, Any] = Field(default_factory=dict)


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


class ConfirmThawaniPaymentRequest(BaseModel):
    order_id: int


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
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as e:
        logger.exception("_decimal_from_value_failed", error=str(e))
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
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as e:
        logger.exception("_json_load_dict_failed", error=str(e))
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
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as e:
        logger.exception("_json_load_currency_list_failed", error=str(e))
        return []
    return _normalize_currency_codes([str(item) for item in parsed]) if isinstance(parsed, list) else []


def normalize_checkout_payment_method(value: str | None) -> str:
    normalized = str(value or "card").strip().lower()
    if normalized == "stripe":
        return "card"
    return normalized


def gateway_code_for_payment_method(payment_method: str | None) -> Optional[str]:
    return ORDER_PAYMENT_METHOD_GATEWAY_MAP.get(normalize_checkout_payment_method(payment_method))


def _normalized_payment_method(order: Order) -> str:
    return str(getattr(order, "payment_method", "card") or "card").strip().lower()

