"""payments domain event subscribers.

Per Law 3, payments is a *publishing* domain that emits
``PaymentAuthorized`` / ``PaymentCaptured`` / ``PaymentFailed`` / ``PaymentRefunded``
events; consumers (orders, finance, comms) subscribe here. Wire once at app
startup via ``register_payments_subscribers(publisher)`` from ``lifespan.py``.
"""
from __future__ import annotations

import logging
from typing import Any

from infrastructure.messaging.events.event_publisher import EventPublisher

from domains.payments.events import (
    PaymentAuthorized,
    PaymentCaptured,
    PaymentFailed,
    PaymentRefunded,
)

logger = logging.getLogger(__name__)


def _on_payment_authorized(event: Any) -> None:
    """Order marked as authorized but pending capture."""
    logger.info(
        "payment authorized: payment_id=%s order_id=%s country=%s amount=%s",
        getattr(event, "payment_id", "?"),
        getattr(event, "order_id", "?"),
        getattr(event, "country_code", "?"),
        getattr(event, "amount", "?"),
    )
    # Future: mark order as authorized in orders domain (via ports or by
    # raising OrderAuthorized event downstream).


def _on_payment_captured(event: Any) -> None:
    """Funds settled — downstream effects: order confirmation, finance accrual."""
    logger.info(
        "payment captured: payment_id=%s order_id=%s country=%s amount=%s",
        getattr(event, "payment_id", "?"),
        getattr(event, "order_id", "?"),
        getattr(event, "country_code", "?"),
        getattr(event, "amount", "?"),
    )
    # Future: trigger OrderConfirmed and FinanceCommissionAccrued events.


def _on_payment_failed(event: Any) -> None:
    """Payment failed — log + alert + cancel pending order."""
    logger.warning(
        "payment failed: payment_id=%s order_id=%s error=%s",
        getattr(event, "payment_id", "?"),
        getattr(event, "order_id", "?"),
        getattr(event, "error_code", "?"),
    )
    # Future: cancel order in pending state, send notification via comms.


def _on_payment_refunded(event: Any) -> None:
    """Refund processed — downstream: ledger reversal + customer comms."""
    logger.info(
        "payment refunded: payment_id=%s refund_id=%s amount=%s",
        getattr(event, "payment_id", "?"),
        getattr(event, "refund_id", "?"),
        getattr(event, "amount", "?"),
    )
    # Future: post refund ledger entry + send refund email/SMS.


def register_payments_subscribers(publisher: EventPublisher) -> None:
    """Register all payments-domain event listeners."""
    publisher.register_listener(PaymentAuthorized, _on_payment_authorized)
    publisher.register_listener(PaymentCaptured, _on_payment_captured)
    publisher.register_listener(PaymentFailed, _on_payment_failed)
    publisher.register_listener(PaymentRefunded, _on_payment_refunded)
    logger.info("Payments domain event subscribers registered")
