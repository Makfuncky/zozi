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


def publish(event_type: str, payload: dict, propagate: bool = False):
    """Deliver *payload* to all subscribers of *event_type* (best-effort).

    Returns the value produced by the handlers so a *requested* intent can hand
    the caller back the result of the delegated write (preserving the direct-call
    contract during the Law-3 migration). With a single subscriber the handler's
    return value is passed through; with several, a list of results is returned;
    with none, ``None``.

    By default a handler exception is caught, logged and replaced with ``None`` so
    one failing subscriber cannot break its siblings (needed for fire-and-forget
    broadcasts such as finance/supplier notifications). Callers that delegate a
    real write intent and must surface failures (e.g. governance ``*_requested``
    intents) should pass ``propagate=True`` so the error bubbles up to the caller
    instead of being silently swallowed.
    """
    results = []
    for handler in list(_subscribers.get(event_type, [])):
        try:
            results.append(handler(payload))
        except Exception:  # noqa: BLE001 - one bad subscriber must not break others
            if propagate:
                raise
            logger.exception("event handler failed for %s", event_type)
            results.append(None)
    if len(results) == 1:
        return results[0]
    if len(results) > 1:
        return results
    return None


def publish_order_status_changed(order_id: int, status: str, old_status: str | None = None) -> None:
    publish(EVENT_ORDER_STATUS_CHANGED, {"order_id": order_id, "status": status, "old_status": old_status})


def publish_order_refunded(order_id: int, source: str = "admin") -> None:
    publish(EVENT_ORDER_REFUNDED, {"order_id": order_id, "source": source})

# Event-name constants live in the shared event contract (this exempt data
# layer) so domains can reference them without importing sibling domains.
# Mirrors the definition in domains.finance.events.
EVENT_FINANCE_BADGE_BILLING_PAID = "finance.badge_billing_paid"
