from __future__ import annotations

from decimal import Decimal
from datetime import datetime
from enum import Enum
from typing import Any, Optional, Union

from pydantic import BaseModel, Field


class ZoziEventStatus(str, Enum):
    """Normalized payment event statuses."""
    PAYMENT_CAPTURED = "payment_captured"
    PAYMENT_FAILED = "payment_failed"
    REFUND_SUCCEEDED = "refund_succeeded"
    REFUND_FAILED = "refund_failed"
    CHARGEBACK_OPENED = "chargeback_opened"
    CHARGEBACK_CLOSED = "chargeback_closed"


class ZoziEventType(str, Enum):
    """Normalized event types for the Zozi system."""
    PAYMENT_SUCCESS = "payment_success"
    PAYMENT_FAILURE = "payment_failure"
    REFUND = "refund"
    CHARGEBACK = "chargeback"


class ZoziPaymentEvent(BaseModel):
    """
    Universal webhook normalizer schema.
    
    Every payment gateway webhook is translated to this internal schema.
    The Order Controller and Treasury Engine only interact with this model.
    """
    provider_code: str = Field(..., description="Gateway provider (e.g., 'stripe', 'tap', 'thawani')")
    gateway_event_id: str = Field(..., description="Unique event ID from the gateway")
    event_type: ZoziEventType = Field(..., description="Normalized event type")
    status: ZoziEventStatus = Field(..., description="Normalized payment status")
    environment: str = Field(default="live", description="Either 'sandbox' or 'live'")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When the event occurred at gateway")
    
    zozi_order_id: Optional[str] = Field(None, description="Zozi order ID extracted from metadata")
    gateway_transaction_id: Optional[str] = Field(None, description="Gateway's transaction/reference ID")
    gateway_customer_id: Optional[str] = Field(None, description="Customer ID at the gateway for recurring charges")
    
    gross_amount: Decimal = Field(..., description="Total amount charged to customer")
    currency: str = Field(..., description="ISO 4217 currency code (e.g., 'SAR', 'OMR')")
    gateway_fee: Decimal = Field(default=Decimal("0"), description="Gateway fee deducted")
    net_settlement: Decimal = Field(..., description="Amount that will hit the bank account")
    
    fraud_score: Optional[int] = Field(None, description="Gateway's risk score (0-100)")
    three_ds_status: Optional[str] = Field(None, description="3DS status: 'passed', 'failed', 'attempted', 'not_required'")
    avs_result: Optional[str] = Field(None, description="Address Verification System result")
    
    raw_payload: dict[str, Any] = Field(default_factory=dict, description="Original webhook payload for audit")


class ZoziRefundEvent(BaseModel):
    """Normalized refund event data."""
    provider_code: str
    gateway_event_id: str
    gateway_refund_id: str
    zozi_order_id: Optional[str] = None
    gateway_transaction_id: Optional[str] = None
    amount: Decimal
    currency: str
    refund_reason: Optional[str] = None
    raw_payload: dict[str, Any] = Field(default_factory=dict)


class ZoziChargebackEvent(BaseModel):
    """Normalized chargeback event data."""
    provider_code: str
    gateway_event_id: str
    gateway_chargeback_id: str
    zozi_order_id: Optional[str] = None
    gateway_transaction_id: Optional[str] = None
    amount: Decimal
    currency: str
    reason: Optional[str] = None
    raw_payload: dict[str, Any] = Field(default_factory=dict)

