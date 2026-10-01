"""Normalized payment webhook event models.

These are the provider-agnostic event carriers produced by gateway adapter
``normalize_webhook_payload`` implementations and consumed by
``services/gateways/webhook_processor.py``. ``event_type`` and ``status`` are
enums so callers can safely read ``.value`` when persisting the normalized row.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class WebhookEventType(str, Enum):
    PAYMENT = "payment"
    REFUND = "refund"
    CHARGEBACK = "chargeback"
    UNKNOWN = "unknown"


class WebhookStatus(str, Enum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    PENDING = "pending"
    DISPUTED = "disputed"
    UNKNOWN = "unknown"


class _BaseWebhookEvent(BaseModel):
    provider_code: str
    gateway_event_id: str
    event_type: WebhookEventType = WebhookEventType.UNKNOWN
    status: WebhookStatus = WebhookStatus.UNKNOWN
    environment: str = "test"
    timestamp: Optional[datetime] = None
    zozi_order_id: Optional[str] = None
    gateway_transaction_id: Optional[str] = None
    gateway_customer_id: Optional[str] = None
    gross_amount: Optional[float] = None
    currency: Optional[str] = None
    gateway_fee: Optional[float] = None
    net_settlement: Optional[float] = None
    fraud_score: Optional[float] = None
    three_ds_status: Optional[str] = None
    avs_result: Optional[str] = None
    raw_payload: Optional[dict[str, Any]] = None


class ZoziPaymentEvent(_BaseWebhookEvent):
    event_type: WebhookEventType = WebhookEventType.PAYMENT


class ZoziRefundEvent(_BaseWebhookEvent):
    event_type: WebhookEventType = WebhookEventType.REFUND


class ZoziChargebackEvent(_BaseWebhookEvent):
    event_type: WebhookEventType = WebhookEventType.CHARGEBACK
