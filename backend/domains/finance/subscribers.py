"""finance domain event subscribers.

Per Law 3, cross-domain *writes* happen only by consuming events here. This module
registers listeners on the canonical ``event_bus`` so the finance domain can
react to events without importing sibling domains directly.

Wire it at app startup by importing this module, or call
``register_finance_subscribers()`` explicitly from ``lifespan.py``.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict

from infrastructure.messaging.events.event_bus import subscribe

logger = logging.getLogger(__name__)


def _ensure_implemented(feature: str) -> None:
    if os.getenv("APP_ENV", "development").lower() != "development":
        raise NotImplementedError(f"{feature} event handler is not implemented")


def _on_payment_confirmed(payload: Dict[str, Any]) -> None:
    """React to a payment confirmed in the payments domain.

    The finance domain accrues commission and posts the corresponding
    transaction-ledger entry once a payment settles.
    """
    _ensure_implemented("payments.confirmed")
    logger.info(
        "payment confirmed: order_id=%s amount=%s — accrue commission",
        payload.get("order_id", "?"),
        payload.get("amount", "?"),
    )


def _on_payment_refunded(payload: Dict[str, Any]) -> None:
    """React to a payment refunded in the payments domain."""
    _ensure_implemented("payments.refunded")
    logger.info(
        "payment refunded: order_id=%s amount=%s — post refund ledger entry",
        payload.get("order_id", "?"),
        payload.get("amount", "?"),
    )


def _on_order_completed(payload: Dict[str, Any]) -> None:
    """React to an order completion in the orders domain."""
    _ensure_implemented("orders.order.completed")
    logger.info(
        "order completed: order_id=%s — post settlement journal",
        payload.get("order_id", "?"),
    )


def register_finance_subscribers() -> None:
    """Register all finance-domain event listeners on the canonical event bus."""
    subscribe("payments.confirmed", _on_payment_confirmed)
    subscribe("payments.refunded", _on_payment_refunded)
    subscribe("orders.order.completed", _on_order_completed)
    logger.info("Finance domain event subscribers registered")
