"""payments domain — request/response DTOs.

Pydantic schemas for payment intents, refunds, and webhook payloads. These are
the wire-format contracts used by ``modules/*/routers/payments.py`` (Law 2:
routers stay thin, schemas are the boundary).

The canonical DB models live in ``domains/payments/models/payment_models.py``
(``payment_methods``, ``payment_attempts``, ``refunds``, ``payment_intents``)
and the finance-owned ``finance.payments`` / ``finance.payouts`` projections.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


# ── Shared enums ─────────────────────────────────────────────────────────────

PROVIDERS = ("stripe", "tap", "paypal", "paytabs", "thawani")
REFUND_STATUSES = ("pending", "succeeded", "failed", "cancelled")
PAYMENT_INTENT_STATUSES = (
    "requires_payment_method",
    "requires_confirmation",
    "requires_action",
    "processing",
    "requires_capture",
    "canceled",
    "succeeded",
)


# ── Payment Intent ───────────────────────────────────────────────────────────

class PaymentIntentCreate(BaseModel):
    """Body for POST /api/v1/<module>/payments/intents."""
    order_id: int = Field(..., gt=0)
    amount: Decimal = Field(..., gt=0, description="Must be > 0 (Law 19: money in NUMERIC)")
    currency: str = Field(..., min_length=3, max_length=3, description="ISO-4217 (AED, SAR, USD, ...)")
    country_code: str = Field(..., min_length=2, max_length=2, description="ISO-3166-1 alpha-2 (AE, SA)")
    provider: str = Field("stripe", description="One of PROVIDERS")
    metadata: Optional[dict[str, Any]] = None
    payment_method_id: Optional[int] = Field(
        None, description="Optional saved payment method from payments.payment_methods"
    )

    @field_validator("provider")
    @classmethod
    def _validate_provider(cls, v: str) -> str:
        if v not in PROVIDERS:
            raise ValueError(f"provider must be one of {PROVIDERS}")
        return v

    @field_validator("currency")
    @classmethod
    def _validate_currency(cls, v: str) -> str:
        return v.upper()

    @field_validator("country_code")
    @classmethod
    def _validate_country(cls, v: str) -> str:
        cc = v.upper()
        if cc not in {"AE", "SA"}:
            raise ValueError("country_code must be AE or SA (Phase G scope)")
        return cc


class PaymentIntentResponse(BaseModel):
    id: int
    order_id: int
    amount: Decimal
    currency: str
    country_code: str
    provider: str
    status: str
    provider_intent_id: Optional[str] = None
    client_secret: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# ── Refund ───────────────────────────────────────────────────────────────────

class RefundCreate(BaseModel):
    """Body for POST /api/v1/<module>/payments/<payment_id>/refunds."""
    amount: Decimal = Field(..., gt=0)
    reason: Optional[str] = Field(None, max_length=200)
    notes: Optional[str] = None


class RefundResponse(BaseModel):
    id: int
    payment_id: int
    country_code: str
    amount: Decimal
    currency: str
    reason: Optional[str] = None
    status: str
    provider: str
    provider_refund_id: Optional[str] = None
    requested_at: datetime
    completed_at: Optional[datetime] = None


# ── Webhook payloads ─────────────────────────────────────────────────────────

class WebhookEnvelope(BaseModel):
    """Generic webhook envelope — every PSP wraps their event payload in this.

    The ``provider`` field picks which parser to use; ``event_type`` is the
    vendor event name (e.g. ``payment_intent.succeeded`` for Stripe,
    ``charge.succeeded`` for Tap, ``PAYMENT.SALE.COMPLETED`` for PayPal).
    """
    provider: str = Field(..., description="stripe | tap | paypal | paytabs | thawani")
    event_type: str = Field(..., min_length=1, max_length=120)
    event_id: Optional[str] = Field(None, description="Vendor-side id for idempotency")
    livemode: bool = False
    received_at: datetime = Field(default_factory=datetime.utcnow)
    data: dict[str, Any] = Field(default_factory=dict)

    @field_validator("provider")
    @classmethod
    def _validate_provider(cls, v: str) -> str:
        if v not in PROVIDERS:
            raise ValueError(f"provider must be one of {PROVIDERS}")
        return v


# ── Payment Method (customer-saved) ──────────────────────────────────────────

class PaymentMethodResponse(BaseModel):
    id: int
    user_id: int
    country_code: str
    provider: str
    method_type: str
    brand: Optional[str] = None
    last4: Optional[str] = None
    expires_at: Optional[datetime] = None
    is_default: bool = False
    created_at: datetime