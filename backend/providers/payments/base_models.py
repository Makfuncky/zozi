"""Payment gateway result/value models.

Shared pydantic response models returned by gateway adapters and consumed by
``services/treasury/payment_engine.py``. Kept dependency-light (no models/db
imports) so adapters and the registry can use them without a database session.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class ConnectionTestResult(BaseModel):
    """Result of a gateway connectivity / credentials test."""

    success: bool
    message: str = ""
    details: dict[str, Any] = Field(default_factory=dict)
    tested_at: Optional[datetime] = None


class PaymentResult(BaseModel):
    """Result of a ``process_payment`` call against a gateway adapter."""

    success: bool
    transaction_id: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    gateway_response: dict[str, Any] = Field(default_factory=dict)


class RefundResult(BaseModel):
    """Result of a ``process_refund`` call against a gateway adapter."""

    success: bool
    refund_id: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    gateway_response: dict[str, Any] = Field(default_factory=dict)
