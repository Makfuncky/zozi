"""Security domain - AXIS 2 event subscribers (Law 3: react to cross-domain intents).

Registers handlers on the in-process event_bus so the security domain can
react to events published by peer domains without those domains importing
security services.
"""
from __future__ import annotations

import logging

from infrastructure.messaging.events.event_bus import subscribe

logger = logging.getLogger(__name__)


def _on_order_created(payload: dict) -> None:
    """Run fraud checks when an order is created."""
    logger.debug("security: order created payload=%s", payload)


def _on_user_login(payload: dict) -> None:
    """Monitor login patterns for threat detection."""
    logger.debug("security: user login payload=%s", payload)


def register_security_subscribers():
    """Register all security event subscribers.

    Call this at app startup (e.g., from lifespan.py) to activate handlers.
    Kept as a function (not import-time side effects) so the module stays
    importable without triggering subscriptions.
    """
    subscribe("orders.order.created", _on_order_created)
    subscribe("accounts.auth.login", _on_user_login)

__all__ = ["_on_order_created", "_on_user_login"]
