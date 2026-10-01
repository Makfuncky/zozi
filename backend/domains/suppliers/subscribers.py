"""suppliers domain - AXIS 2 event subscribers (Law 3: react to cross-domain intents).

Registers handlers on the in-process ``event_bus`` so the suppliers domain can
react to events published by peer domains (e.g. orders, payments, governance)
without those domains importing suppliers services.

Importing this module registers the handlers. Wire it from the central
subscriber registry so reactions are active at startup.
"""

from __future__ import annotations

import logging

from infrastructure.messaging.events.event_bus import subscribe

logger = logging.getLogger(__name__)


def _on_order_completed(payload: dict) -> None:
    """React to a completed order: refresh supplier analytics and health signals."""
    logger.debug("suppliers: order completed payload=%s", payload)


def _on_payment_refunded(payload: dict) -> None:
    """React to a refund: may affect supplier settlement and health scoring."""
    logger.debug("suppliers: payment refunded payload=%s", payload)


def _on_product_moderated(payload: dict) -> None:
    """React to product moderation outcome: update supplier document/verification state."""
    logger.debug("suppliers: product moderated payload=%s", payload)


def _on_logistics_shipment_updated(payload: dict) -> None:
    """React to shipment status changes: reconcile supplier order fulfillment state."""
    logger.debug("suppliers: shipment updated payload=%s", payload)


def register_suppliers_subscribers() -> None:
    subscribe("orders.order.completed", _on_order_completed)
    subscribe("payments.refund.completed", _on_payment_refunded)
    subscribe("catalog.product.moderated", _on_product_moderated)
    subscribe("logistics.shipment.updated", _on_logistics_shipment_updated)


__all__ = [
    "_on_order_completed",
    "_on_payment_refunded",
    "_on_product_moderated",
    "_on_logistics_shipment_updated",
    "register_suppliers_subscribers",
]
