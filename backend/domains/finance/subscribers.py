"""finance domain event subscribers.

Per Law 3, cross-domain *writes* happen only by consuming events here. This module
registers listeners against the shared ``EventPublisher``. Wire it at boot by calling
``register_finance_subscribers(publisher)`` from ``lifespan.py`` (kept optional so the
domain stays importable without side effects).
"""

from __future__ import annotations

import logging
from typing import Any

from infrastructure.messaging.events.event_publisher import EventPublisher

logger = logging.getLogger(__name__)


def _on_payment_confirmed(event: Any) -> None:
    """React to a payment confirmed in the payments domain.

    The finance domain accrues commission and posts the corresponding
    transaction-ledger entry once a payment settles.
    """
    logger.info(
        "payment confirmed: order_id=%s amount=%s — accrue commission",
        getattr(event, "order_id", "?"),
        getattr(event, "amount", "?"),
    )
    # Future: post commission accrual to TransactionLedger, update balances.


def _on_payment_refunded(event: Any) -> None:
    """React to a payment refunded in the payments domain."""
    logger.info(
        "payment refunded: order_id=%s amount=%s — post refund ledger entry",
        getattr(event, "order_id", "?"),
        getattr(event, "amount", "?"),
    )
    # Future: post RefundLedger entry, reverse commission accrual.


def _on_order_completed(event: Any) -> None:
    """React to an order completion in the orders domain."""
    logger.info(
        "order completed: order_id=%s — post settlement journal",
        getattr(event, "order_id", "?"),
    )
    # Future: post SupplierSettlement journal entry when order fulfils.


def register_finance_subscribers(publisher: EventPublisher) -> None:
    """Register all finance-domain event listeners.

    Called once at app startup from ``lifespan.py``. Importing the event
    classes lazily avoids hard dependencies on publishing domains that may
    not be wired in every deployment.
    """
    # Payments-domain events we react to.
    try:
        from infrastructure.messaging.events import PaymentConfirmedEvent
        from infrastructure.messaging.events import PaymentRefundedEvent

        publisher.register_listener(PaymentConfirmedEvent, _on_payment_confirmed)
        publisher.register_listener(PaymentRefundedEvent, _on_payment_refunded)
    except ImportError:
        logger.debug("Payment events not available — skipping finance payment listeners")

    # Orders-domain events we react to (resolved lazily to avoid import cycle).
    try:
        from domains.orders.events import OrderCompleted

        publisher.register_listener(OrderCompleted, _on_order_completed)
    except ImportError:
        logger.debug("OrderCompleted event not available — skipping finance order listener")

    logger.info("Finance domain event subscribers registered")
