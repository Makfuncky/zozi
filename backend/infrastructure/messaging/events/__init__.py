"""Domain events for Zozi E-commerce.

This module contains domain event classes that represent significant
business domain changes in the Zozi e-commerce platform.

Canonical event bus
--------------------
``event_bus`` is the single canonical event bus (WIR-028).  All new code
should import ``publish`` / ``subscribe`` from ``event_bus`` directly.

``EventPublisher`` is retained as a deprecated backwards-compatible adapter
for domain subscribers that have not yet migrated.  It will be removed once
all callers have switched.
"""
from __future__ import annotations

from .event_bus import (
    EVENT_FINANCE_BADGE_BILLING_PAID,
    EVENT_ORDER_REFUNDED,
    EVENT_ORDER_STATUS_CHANGED,
    clear,
    publish,
    publish_order_refunded,
    publish_order_status_changed,
    shutdown,
    subscribe,
    unsubscribe,
)
from .event_publisher import EventPublisher
from .payment_events import (
    PaymentConfirmedEvent,
    PaymentFailedEvent,
    PaymentRefundedEvent,
)

# Canonical, process-wide event publisher singleton (deprecated; use event_bus).
_event_publisher = EventPublisher()

__all__ = [
    # Canonical event bus (WIR-028).
    "publish",
    "subscribe",
    "unsubscribe",
    "clear",
    "shutdown",
    "publish_order_status_changed",
    "publish_order_refunded",
    # Canonical event-name constants.
    "EVENT_ORDER_STATUS_CHANGED",
    "EVENT_ORDER_REFUNDED",
    "EVENT_FINANCE_BADGE_BILLING_PAID",
    # Payment event classes.
    "PaymentConfirmedEvent",
    "PaymentFailedEvent",
    "PaymentRefundedEvent",
    # Deprecated adapter.
    "EventPublisher",
    "_event_publisher",
]
