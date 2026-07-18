from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Union

from .base_models import ConnectionTestResult, PaymentResult, RefundResult
from .webhook_models import ZoziPaymentEvent, ZoziRefundEvent, ZoziChargebackEvent


class BasePaymentGateway(ABC):
    """Abstract base for all payment gateway adapters.

    Subclasses are auto-discovered by PaymentGatewayRegistry.
    Each subclass must set ``gateway_id`` to a unique identifier
    that matches the ``gateway_id`` field in a country's
    ``payment_gateways_json`` configuration.
    """

    gateway_id: str = ""
    display_name: str = ""

    @abstractmethod
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
        """Initiate a payment and return the result."""

    @abstractmethod
    def process_refund(
        self,
        transaction_id: str,
        amount: float | None,
        credentials: dict[str, Any],
        *,
        reason: str = "",
        **kwargs: Any,
    ) -> RefundResult:
        """Issue a refund against a previous transaction."""

    @abstractmethod
    def verify_webhook_signature(
        self,
        raw_body: bytes,
        headers: dict[str, str],
        webhook_secret: str,
    ) -> bool:
        """Verify the cryptographic signature of an incoming webhook."""

    @abstractmethod
    def normalize_webhook_payload(
        self,
        raw_body: bytes,
        headers: dict[str, str],
    ) -> Union[ZoziPaymentEvent, ZoziRefundEvent, ZoziChargebackEvent]:
        """Translate gateway-specific webhook into normalized Zozi schema."""

    def validate_credentials(self, credentials: dict[str, Any]) -> bool:
        """Return True if the credential dict has all required keys."""
        return True

    def test_connection(self, credentials: dict[str, Any]) -> ConnectionTestResult:
        """Test connectivity with the gateway using the provided credentials."""
        return ConnectionTestResult(success=True, message="No test implemented")

