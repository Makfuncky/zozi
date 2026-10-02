"""payments domain event subscribers.

Per Law 3, payments is a *publishing* domain that emits
``PaymentAuthorized`` / ``PaymentCaptured`` / ``PaymentFailed`` / ``PaymentRefunded``
events; consumers (orders, finance, comms) subscribe here. Wire once at app
startup by importing this module or calling ``register_payments_subscribers()``
from ``lifespan.py``.
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from infrastructure.messaging.events.event_bus import subscribe

logger = logging.getLogger(__name__)


def _on_payment_authorized(payload: Dict[str, Any]) -> None:
    """Order marked as authorized but pending capture."""
    logger.info(
        "payment authorized: payment_id=%s order_id=%s country=%s amount=%s",
        payload.get("payment_id", "?"),
        payload.get("order_id", "?"),
        payload.get("country_code", "?"),
        payload.get("amount", "?"),
    )
    # Future: mark order as authorized in orders domain (via ports or by
    # raising OrderAuthorized event downstream).


def _on_payment_captured(payload: Dict[str, Any]) -> None:
    """Funds settled — downstream effects: order confirmation, finance accrual."""
    logger.info(
        "payment captured: payment_id=%s order_id=%s country=%s amount=%s",
        payload.get("payment_id", "?"),
        payload.get("order_id", "?"),
        payload.get("country_code", "?"),
        payload.get("amount", "?"),
    )
    # Future: trigger OrderConfirmed and FinanceCommissionAccrued events.


def _on_payment_failed(payload: Dict[str, Any]) -> None:
    """Payment failed — log + alert + cancel pending order."""
    logger.warning(
        "payment failed: payment_id=%s order_id=%s error=%s",
        payload.get("payment_id", "?"),
        payload.get("order_id", "?"),
        payload.get("error_code", "?"),
    )
    # Future: cancel order in pending state, send notification via comms.


def _on_payment_refunded(payload: Dict[str, Any]) -> None:
    """Refund processed — downstream: ledger reversal + customer comms."""
    logger.info(
        "payment refunded: payment_id=%s refund_id=%s amount=%s",
        payload.get("payment_id", "?"),
        payload.get("refund_id", "?"),
        payload.get("amount", "?"),
    )
    # Future: post refund ledger entry + send refund email/SMS.


def register_payments_subscribers() -> None:
    """Register all payments-domain event listeners on the canonical event bus."""
    subscribe("payments.authorized", _on_payment_authorized)
    subscribe("payments.captured", _on_payment_captured)
    subscribe("payments.failed", _on_payment_failed)
    subscribe("payments.refunded", _on_payment_refunded)
    logger.info("Payments domain event subscribers registered")
