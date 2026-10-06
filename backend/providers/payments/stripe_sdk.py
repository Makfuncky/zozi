"""Stripe SDK access point for the provider layer.

The stripe Python SDK is an external integration. Service-layer code must not
import stripe directly; it should reach it through this provider module so that
all third-party payment SDK usage is centralized behind the provider boundary.
"""

from __future__ import annotations

import logging

from infrastructure.observability.circuit_breaker import CircuitBreakerError, get_circuit_breaker

HAS_STRIPE = False
stripe = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


def _load_stripe():
    """Lazily import stripe; return the module or None."""
    global stripe, HAS_STRIPE
    if stripe is not None:
        return stripe
    try:
        import stripe as _stripe  # type: ignore[import-untyped]
        stripe = _stripe
        HAS_STRIPE = True
        return stripe
    except ImportError:  # pragma: no cover - optional SDK
        HAS_STRIPE = False
        stripe = None
        return None


_stripe_breaker = get_circuit_breaker("stripe", failure_threshold=5, recovery_timeout=30)

__all__ = ["stripe", "HAS_STRIPE"]


def refund_payment_intent(payment_intent_id: str, api_key: str = "") -> dict:
    """Refund a payment intent via Stripe SDK."""
    _sdk = _load_stripe()
    if _sdk is not None:
        try:
            return _create_refund(payment_intent_id)
        except CircuitBreakerError as exc:
            logger.warning(
                "stripe_circuit_open",
                payment_intent_id=payment_intent_id,
                error=str(exc),
            )
            raise
        except Exception as exc:
            logger.warning("Failed to refund payment intent %s: %s", payment_intent_id, exc)
            raise
    return {"id": "stub_refund", "status": "succeeded"}


# Lazily resolved: _create_refund is defined after _load_stripe so it can
# reference the stripe module via the loader rather than a bare name.
def _create_refund(payment_intent_id: str) -> dict:
    _sdk = _load_stripe()
    if _sdk is None:
        raise RuntimeError("Stripe SDK is not available")
    return _sdk.Refund.create(payment_intent=payment_intent_id)
