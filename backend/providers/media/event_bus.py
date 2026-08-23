"""In-process event bus for cross-domain decoupling.

Lives in the circuit-exempt ``data`` layer so first-party domains can publish
and subscribe to events without importing one another (bounded context). This
is the sanctioned mechanism for breaking dependency cycles: a domain publishes
an intent here instead of calling a sibling domain's service directly.

``data`` is an exempt layer in the architecture audit, so importing this module
never creates a domain dependency edge.
"""
from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List

logger = logging.getLogger(__name__)

_subscribers: Dict[str, List[Callable[[dict], None]]] = {}

EVENT_ORDER_STATUS_CHANGED = "order.status_changed"
EVENT_ORDER_REFUNDED = "order.refunded"


def subscribe(event_type: str, handler: Callable[[dict], None]) -> None:
    """Register *handler* to receive every published *event_type* payload."""
    _subscribers.setdefault(event_type, []).append(handler)


def publish(event_type: str, payload: dict) -> None:
    """Deliver *payload* to all subscribers of *event_type* (best-effort)."""
    for handler in list(_subscribers.get(event_type, [])):
        try:
            handler(payload)
        except Exception:  # noqa: BLE001 - one bad subscriber must not break others
            logger.exception("event handler failed for %s", event_type)


def publish_order_status_changed(order_id: int, status: str, old_status: str | None = None) -> None:
    publish(EVENT_ORDER_STATUS_CHANGED, {"order_id": order_id, "status": status, "old_status": old_status})


def publish_order_refunded(order_id: int, source: str = "admin") -> None:
    publish(EVENT_ORDER_REFUNDED, {"order_id": order_id, "source": source})
