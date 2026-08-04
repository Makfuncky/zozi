from enum import Enum
from typing import Optional, Any

from pydantic import BaseModel, Field


class PaymentEventType(str, Enum):
    PAYMENT_SUCCESS = "payment.success"
    PAYMENT_FAILED = "payment.failed"
    REFUND_SUCCESS = "refund.success"
    REFUND_FAILED = "refund.failed"
    CHARGEBACK = "chargeback"


class ZoziPaymentEvent(BaseModel):
    gateway_id: str
    event_type: PaymentEventType
    transaction_id: Optional[str] = None
    order_id: Optional[int] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    payload: dict[str, Any] = Field(default_factory=dict)


class ZoziRefundEvent(BaseModel):
    gateway_id: str
    transaction_id: str
    refund_id: Optional[str] = None
    amount: Optional[float] = None
    reason: Optional[str] = None
    payload: dict[str, Any] = Field(default_factory=dict)


class ZoziChargebackEvent(BaseModel):
    gateway_id: str
    transaction_id: str
    reason: str
    amount: Optional[float] = None
    payload: dict[str, Any] = Field(default_factory=dict)