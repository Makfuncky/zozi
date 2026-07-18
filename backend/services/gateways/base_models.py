from __future__ import annotations

from typing import Any
from decimal import Decimal
from datetime import datetime


class PaymentResult:
    def __init__(
        self,
        *,
        success: bool,
        transaction_id: str | None = None,
        gateway_ref: str | None = None,
        amount: Decimal | None = None,
        currency: str | None = None,
        status: str = "pending",
        error_code: str | None = None,
        error_message: str | None = None,
        raw_response: dict[str, Any] | None = None,
        redirect_url: str | None = None,
    ):
        self.success = success
        self.transaction_id = transaction_id
        self.gateway_ref = gateway_ref
        self.amount = amount
        self.currency = currency
        self.status = status
        self.error_code = error_code
        self.error_message = error_message
        self.raw_response = raw_response or {}
        self.redirect_url = redirect_url


class RefundResult:
    def __init__(
        self,
        *,
        success: bool,
        refund_id: str | None = None,
        gateway_ref: str | None = None,
        amount: Decimal | None = None,
        status: str = "pending",
        error_code: str | None = None,
        error_message: str | None = None,
    ):
        self.success = success
        self.refund_id = refund_id
        self.gateway_ref = gateway_ref
        self.amount = amount
        self.status = status
        self.error_code = error_code
        self.error_message = error_message


class ConnectionTestResult:
    def __init__(
        self,
        *,
        success: bool,
        message: str = "",
        latency_ms: float | None = None,
    ):
        self.success = success
        self.message = message
        self.latency_ms = latency_ms

