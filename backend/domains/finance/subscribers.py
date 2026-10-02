"""finance domain event subscribers.

Per Law 3, cross-domain *writes* happen only by consuming events here. This module
registers listeners on the canonical ``event_bus`` so the finance domain can
react to events without importing sibling domains directly.

Wire it at app startup by importing this module, or call
``register_finance_subscribers()`` explicitly from ``lifespan.py``.
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from infrastructure.messaging.events.event_bus import subscribe

logger = logging.getLogger(__name__)


def _on_payment_confirmed(payload: Dict[str, Any]) -> None:
    """React to a payment confirmed in the payments domain.

    The finance domain accrues commission and posts the corresponding
    transaction-ledger entry once a payment settles.
    """
    logger.info(
        "payment confirmed: order_id=%s amount=%s — accrue commission",
        payload.get("order_id", "?"),
        payload.get("amount", "?"),
    )
    # Future: post commission accrual to TransactionLedger, update balances.


def _on_payment_refunded(payload: Dict[str, Any]) -> None:
    """React to a payment refunded in the payments domain."""
    logger.info(
        "payment refunded: order_id=%s amount=%s — post refund ledger entry",
        payload.get("order_id", "?"),
        payload.get("amount", "?"),
    )
    # Future: post RefundLedger entry, reverse commission accrual.


def _on_order_completed(payload: Dict[str, Any]) -> None:
    """React to an order completion in the orders domain."""
    logger.info(
        "order completed: order_id=%s — post settlement journal",
        payload.get("order_id", "?"),
    )
    # Future: post SupplierSettlement journal entry when order fulfils.


def register_finance_subscribers() -> None:
    """Register all finance-domain event listeners on the canonical event bus."""
    subscribe("payments.confirmed", _on_payment_confirmed)
    subscribe("payments.refunded", _on_payment_refunded)
    subscribe("orders.order.completed", _on_order_completed)
    logger.info("Finance domain event subscribers registered")
