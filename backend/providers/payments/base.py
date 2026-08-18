"""Abstract base class for payment gateway adapters.

Every concrete gateway (Stripe, Tap, PayTabs, PayPal, Thawani, custom) is
expected to subclass ``BasePaymentGateway`` and register itself with
``services/gateways/registry.py``. The orchestration layer
(``services/treasury/payment_engine.py`` and
``services/gateways/webhook_processor.py``) only depends on this interface.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional, Union

from .base_models import ConnectionTestResult, PaymentResult, RefundResult
from .webhook_models import ZoziChargebackEvent, ZoziPaymentEvent, ZoziRefundEvent


# Standard gateway operation keys dispatched through ``dispatch_provider_operation``.
OPERATION_CREATE = "create"
OPERATION_CONFIRM = "confirm"
OPERATION_WEBHOOK = "webhook"


@dataclass
class GatewaySettings:
    """Resolved runtime configuration for a single payment gateway."""

    provider_code: str
    provider_kind: str
    display_name: str
    is_enabled: bool = False
    mode: str = "test"
    public_key: Optional[str] = None
    secret_key: Optional[str] = None
    webhook_secret: Optional[str] = None
    api_base_url: Optional[str] = None
    webhook_url: Optional[str] = None
    supports_customer_checkout: bool = False
    supports_payouts: bool = False

    def is_usable(self) -> bool:
        return bool(self.is_enabled and self.secret_key)


@dataclass
class GatewayDefinition:
    """Registration record for a concrete payment gateway adapter."""

    code: str
    kind: str
    label: str
    module: str
    settings_resolver: Callable[..., Any]
    is_configured: Callable[..., bool]
    operations: dict = field(default_factory=dict)


_REGISTRY: dict = {}


def register_provider(definition: GatewayDefinition) -> None:
    """Register a gateway adapter under its ``code``."""
    _REGISTRY[definition.code] = definition


def get_provider(code: str) -> Optional[GatewayDefinition]:
    """Look up a registered gateway adapter by code."""
    return _REGISTRY.get(code)


def dispatch_provider_operation(code: str, operation: str, *args: Any, **kwargs: Any) -> Any:
    """Dispatch a standard operation to the registered gateway adapter."""
    definition = get_provider(code)
    if definition is None:
        raise LookupError(f"No payment provider registered for code {code!r}")
    handler = definition.operations.get(operation)
    if handler is None:
        raise LookupError(f"Provider {code!r} does not implement operation {operation!r}")
    return handler(*args, **kwargs)


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
