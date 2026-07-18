from __future__ import annotations

import logging
from typing import Any

import httpx

from .base import BasePaymentGateway
from .base_models import ConnectionTestResult, PaymentResult, RefundResult

logger = logging.getLogger(__name__)


class STCPayAdapter(BasePaymentGateway):
    gateway_id = "stc_pay"
    display_name = "STC Pay"

    def process_payment(
        self,
        amount: float,
        currency: str,
        credentials: dict[str, Any],
        *,
        order_id: int | None = None,
        description: str = "",
        customer: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> PaymentResult:
        return PaymentResult(
            success=False,
            error_code="stc_pay_not_implemented",
            error_message="STC Pay integration requires merchant onboarding. "
                          "Use credentials for API auth when available.",
        )

    def process_refund(
        self,
        transaction_id: str,
        amount: float | None,
        credentials: dict[str, Any],
        *,
        reason: str = "",
        **kwargs: Any,
    ) -> RefundResult:
        return RefundResult(
            success=False,
            error_code="stc_pay_not_implemented",
            error_message="STC Pay refunds not yet implemented.",
        )

