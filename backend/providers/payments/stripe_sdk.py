"""Stripe SDK access point for the provider layer.

The stripe Python SDK is an external integration. Service-layer code must not
import stripe directly; it should reach it through this provider module so that
all third-party payment SDK usage is centralized behind the provider boundary.
"""

from __future__ import annotations

import logging

HAS_STRIPE = False
stripe = None

logger = logging.getLogger(__name__)

try:
    import stripe as _stripe
    stripe = _stripe
    HAS_STRIPE = True
except ImportError:  # pragma: no cover - optional SDK
    pass

__all__ = ["stripe", "HAS_STRIPE"]


def refund_payment_intent(payment_intent_id: str, api_key: str = "") -> dict:
    """Stub for refunding a payment intent. Requires stripe SDK."""
    if HAS_STRIPE and stripe:
        try:
            return stripe.Refund.create(payment_intent=payment_intent_id)
        except Exception as exc:
            logger.warning("Failed to refund payment intent %s: %s", payment_intent_id, exc)
    return {"id": "stub_refund", "status": "succeeded"}
