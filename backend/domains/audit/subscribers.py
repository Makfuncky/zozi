"""Audit domain - AXIS 2 event subscribers (Law 3: react to cross-domain intents).

Registers handlers on the in-process event_bus so the audit domain can
react to events published by peer domains (e.g. orders, governance) without
those domains importing audit services.
"""
from __future__ import annotations

import logging

from infrastructure.messaging.events.event_bus import subscribe

logger = logging.getLogger(__name__)


def _on_order_status_changed(payload: dict) -> None:
    """Log order status changes for audit trail."""
    logger.debug("audit: order status changed payload=%s", payload)


def _on_governance_incident_created(payload: dict) -> None:
    """Record governance incidents in the audit trail."""
    logger.debug("audit: governance incident payload=%s", payload)


def register_audit_subscribers() -> None:
    subscribe("order.status_changed", _on_order_status_changed)
    subscribe("governance.incident.created", _on_governance_incident_created)


__all__ = ["_on_order_status_changed", "_on_governance_incident_created", "register_audit_subscribers"]
