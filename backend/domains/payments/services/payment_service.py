"""payments domain — services.

Phase 2H scaffold: thin wrappers over the canonical payment services that
currently live in ``domains/finance/services/payments/*`` while the long-term
refactor that moves the canonical code into this domain is tracked separately.

Per Law 2 (thin routers) and Law 3 (cross-domain via events/ports), module
routers MUST go through this layer rather than reaching into finance/payments
directly. The functions here intentionally mirror the finance surface so that
the refactor can swap implementations in one place.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any, Optional


# ── Thin wrappers over finance payment service ──────────────────────────────
# These are the sanctioned surface for the ``payments.*`` module routers.
# They call into ``domains/finance/services/payments/payment_orchestrator.py``
# which is the current home of the real implementation.


def create_payment_intent(
    *,
    order_id: int,
    amount: Decimal,
    currency: str,
    country_code: str,
    provider: str = "stripe",
    metadata: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Authorize (not capture) a payment intent for an order.

    Returns a dict with at least: ``payment_id``, ``client_secret``,
    ``provider``, ``status``.
    """
    from domains.finance.ports import create_payment_intent as _create

    return _create(
        order_id=order_id,
        amount=amount,
        currency=currency,
        country_code=country_code,
        provider=provider,
        metadata=metadata or {},
    )


def capture_payment(*, payment_id: int, actor_user_id: int) -> dict[str, Any]:
    """Capture an authorized payment intent."""
    from domains.finance.ports import capture_payment as _capture

    return _capture(payment_id=payment_id, actor_user_id=actor_user_id)


def refund_payment(
    *,
    payment_id: int,
    amount: Decimal,
    reason: str,
    actor_user_id: int,
) -> dict[str, Any]:
    """Refund a captured payment (full or partial)."""
    from domains.finance.ports import refund_payment as _refund

    return _refund(
        payment_id=payment_id,
        amount=amount,
        reason=reason,
        actor_user_id=actor_user_id,
    )
