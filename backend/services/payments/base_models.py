from __future__ import annotations

from typing import Optional, List, Any

from pydantic import BaseModel, Field


class GatewayConfig(BaseModel):
    gateway_id: str
    api_key: Optional[str] = None
    secret_key: Optional[str] = None
    webhook_url: Optional[str] = None
    test_mode: bool = True


class PaymentRequest(BaseModel):
    gateway_id: str
    amount: float
    currency: str = "USD"
    source_id: Optional[str] = None
    order_id: Optional[int] = None
    customer: Optional[dict[str, Any]] = None
    metadata: Optional[dict[str, Any]] = None


class PaymentWebhook(BaseModel):
    gateway_id: str
    event_type: str
    transaction_id: Optional[str] = None
    payload: dict[str, Any] = Field(default_factory=dict)


class RefundRequest(BaseModel):
    transaction_id: str
    amount: Optional[float] = None
    reason: str = ""