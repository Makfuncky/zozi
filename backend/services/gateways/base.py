"""Abstract base class for payment gateway adapters.

Every concrete gateway (Stripe, Tap, PayTabs, PayPal, Thawani, custom) is
expected to subclass ``BasePaymentGateway`` and register itself with
``services/gateways/registry.py``. The orchestration layer
(``services/treasury/payment_engine.py`` and
``services/gateways/webhook_processor.py``) only depends on this interface.
"""
from __future__ import annotations

from typing import Any, Union

from .base_models import ConnectionTestResult, PaymentResult, RefundResult
from .webhook_models import ZoziChargebackEvent, ZoziPaymentEvent, ZoziRefundEvent


class BasePaymentGateway:
    """Contract every gateway adapter must implement."""

    #: Human-readable name shown in admin UI / registry listings.
    display_name: str = "Gateway"

    # ── Credentials ─────────────────────────────────────────────────────────

    def validate_credentials(self, credentials: dict[str, Any]) -> bool:
        """Return True when the supplied credential dict looks usable."""
        return bool(credentials)

    # ── Charges / refunds ───────────────────────────────────────────────────

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
            error_code="not_implemented",
            error_message=f"{type(self).__name__} does not implement process_payment",
        )

    def process_refund(
        self,
        transaction_id: str,
        amount: float | None = None,
        *,
        credentials: dict[str, Any],
        reason: str = "",
        **kwargs: Any,
    ) -> RefundResult:
        return RefundResult(
            success=False,
            error_code="not_implemented",
            error_message=f"{type(self).__name__} does not implement process_refund",
        )

    def test_connection(self, credentials: dict[str, Any]) -> ConnectionTestResult:
        return ConnectionTestResult(
            success=False,
            message=f"{type(self).__name__} does not implement test_connection",
        )

    # ── Webhooks ─────────────────────────────────────────────────────────────

    def verify_webhook_signature(
        self,
        raw_body: bytes,
        headers: dict[str, Any],
        webhook_secret: str,
    ) -> bool:
        """Validate the raw webhook body against its signature.

        Adapters with no signature scheme should treat an empty secret as a
        pass-through (development) and a missing secret as a hard fail.
        """
        if not webhook_secret:
            return False
        return True

    def normalize_webhook_payload(
        self,
        raw_body: bytes,
        headers: dict[str, Any],
    ) -> Union[ZoziPaymentEvent, ZoziRefundEvent, ZoziChargebackEvent]:
        """Parse a provider webhook into a normalized Zozi event."""
        raise NotImplementedError(
            f"{type(self).__name__} does not implement normalize_webhook_payload"
        )
