"""Backwards-compatible re-export shim for the Stripe payment provider.

The provider implementation lives in ``providers.payments.stripe_sdk``; this
module exposes the public function names previously imported directly from
``providers.payments.stripe``.
"""
from __future__ import annotations

from providers.payments.stripe_sdk import (  # noqa: F401
    refund_payment_intent,
)

__all__ = ["refund_payment_intent"]
