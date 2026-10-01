"""Domain events for Zozi E-commerce.

This module contains domain event classes that represent significant
business domain changes in the Zozi e-commerce platform.
"""

from .payment_events import (
    PaymentConfirmedEvent,
    PaymentFailedEvent,
    PaymentRefundedEvent,
)
from .event_publisher import EventPublisher

# Canonical, process-wide event publisher singleton. Both the payment providers
# (via the ``data.events`` shim) and ``lifespan`` listeners resolve to this same
# instance so published events reach their registered handlers.
_event_publisher = EventPublisher()

__all__ = [
    "PaymentConfirmedEvent",
    "PaymentFailedEvent",
    "PaymentRefundedEvent",
    "EventPublisher",
    "_event_publisher",
]
