"""Stripe SDK access point for the provider layer.

The stripe Python SDK is an external integration. Service-layer code must not
import stripe directly; it should reach it through this provider module so that
all third-party payment SDK usage is centralized behind the provider boundary.
"""

from __future__ import annotations

HAS_STRIPE = False
stripe = None

try:
    import stripe as _stripe
    stripe = _stripe
    HAS_STRIPE = True
except ImportError:  # pragma: no cover - optional SDK
    pass

__all__ = ["stripe", "HAS_STRIPE"]
