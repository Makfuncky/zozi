"""customers domain - AXIS 2 event subscribers (Law 3: react to cross-domain intents).

Registers handlers on the in-process ``event_bus`` so the customers domain can
react to events published by peer domains (e.g. orders, payments) without those
domains importing customers services.

Importing this module registers the handlers. Wire it from the domain package
(or the central subscriber registry) once the reaction logic is implemented.
"""

from __future__ import annotations

import logging

from infrastructure.messaging.events.event_bus import subscribe

logger = logging.getLogger(__name__)


def _on_order_completed(payload: dict) -> None:
    """React to a completed order: emit referral/review signals downstream."""
    # PART 1.12: emit referral point events / refresh customer health once the
    # customers write services own that logic.
    logger.debug("customers: order completed payload=%s", payload)


def _on_payment_refunded(payload: dict) -> None:
    """React to a refund: may affect customer health scoring."""
    logger.debug("customers: payment refunded payload=%s", payload)


subscribe("orders.order.completed", _on_order_completed)
subscribe("payments.refund.completed", _on_payment_refunded)


__all__ = ["_on_order_completed", "_on_payment_refunded"]
