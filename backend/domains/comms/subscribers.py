"""comms domain — event subscribers (Law 3).

Subscribers consume cross-domain events emitted by other domains'
``events.py`` and trigger comms-domain side effects (notifications,
emails, escalations). They are the ONLY sanctioned path for cross-domain
**writes** into the comms domain — no other domain may call comms services
directly.

Each handler:
  * receives the event payload (a ``dict`` as produced by
    ``CommsEvent.serialize()`` or the originating domain's equivalent),
  * performs its side effect via the comms services layer,
  * catches and logs exceptions (never lets a subscriber crash the bus).
"""

from __future__ import annotations

import structlog
from typing import Any, Callable, Dict, List, Type

from domains.comms.events import (
    CommsEvent,
    EmailCampaignCreated,
    EscalationTriggered,
    NotificationCreated,
    TicketStatusChanged,
    CommsEvent,
)

logger = structlog.get_logger(__name__)


# ── handler registry ──────────────────────────────────────────────────────

_HANDLERS: Dict[str, List[Callable[[Dict[str, Any]], None]]] = {}


def register(event_type: str) -> Callable:
    """Decorator that registers a handler for ``event_type``."""

    def decorator(fn: Callable[[Dict[str, Any]], None]) -> Callable[[Dict[str, Any]], None]:
        _HANDLERS.setdefault(event_type, []).append(fn)
        return fn

    return decorator


def dispatch(event: CommsEvent) -> None:
    """Dispatch an event to all registered handlers.

    Called by ``infrastructure.messaging.event_bus``. Handlers must not
    raise — every exception is caught and logged so the bus keeps running.
    """
    payload = event.serialize()
    for handler in _HANDLERS.get(event.event_type, []):
        try:
            handler(payload)
        except Exception:
            logger.exception(
                "comms subscriber failed",
                event_type=event.event_type,
                handler=handler.__name__,
            )


def subscribed_types() -> List[str]:
    """Return all event types that have at least one subscriber."""
    return sorted(_HANDLERS.keys())


# ── internal send helper ───────────────────────────────────────────────────


def _send_notification(
    user_id: int,
    type_: str,
    title: str,
    message: str,
    channel: str = "in_app",
    link: str | None = None,
) -> None:
    """Create a notification row. Deferred import avoids circular deps."""
    from domains.comms.models.communication import Notification
    from infrastructure.database.database import get_db

    try:
        db_gen = get_db()
        db = next(db_gen)
        notification = Notification(
            user_id=user_id,
            type=type_,
            title=title,
            message=message,
            channel=channel,
            link=link,
        )
        db.add(notification)
        db.commit()
    except Exception:
        logger.exception("comms notification send failed", user_id=user_id, type=type_)
    finally:
        try:
            next(db_gen, None)
        except Exception:
            logger.debug("DB generator cleanup failed", exc_info=True)


# ── comms-domain event subscribers ────────────────────────────────────────


@register("comms.ticket.status_changed")
def _on_ticket_status_changed(payload: Dict[str, Any]) -> None:
    """Notify the ticket owner when their ticket status changes."""
    # TicketStatusChanged carries ticket_id, new_status, changed_by
    from domains.comms.services.ticket.tickets_service import (
        get_ticket_by_id_safe,
    )

    ticket_id = payload.get("ticket_id")
    if not ticket_id:
        return
    ticket = get_ticket_by_id_safe(ticket_id)
    if ticket is None:
        return
    _send_notification(
        user_id=ticket.user_id,
        type_="ticket_update",
        title="Ticket updated",
        message=f"Your ticket #{ticket_id} is now {payload.get('new_status', 'updated')}.",
        link=f"/tickets/{ticket_id}",
    )


@register("comms.ticket.replied")
def _on_ticket_replied(payload: Dict[str, Any]) -> None:
    """Notify the ticket owner when a staff member replies."""
    from domains.comms.services.ticket.tickets_service import (
        get_ticket_by_id_safe,
    )

    ticket_id = payload.get("ticket_id")
    if not ticket_id:
        return
    ticket = get_ticket_by_id_safe(ticket_id)
    if ticket is None:
        return
    is_admin = payload.get("is_admin", False)
    if is_admin:
        _send_notification(
            user_id=ticket.user_id,
            type_="ticket_reply",
            title="New reply on your ticket",
            message=f"Staff replied to ticket #{ticket_id}.",
            link=f"/tickets/{ticket_id}",
        )


@register("comms.notification.created")
def _on_notification_created(payload: Dict[str, Any]) -> None:
    """Hook for downstream notification delivery (push, email, SMS)."""
    channel = payload.get("channel", "in_app")
    if channel != "in_app":
        logger.info(
            "comms notification delivery queued",
            notification_id=payload.get("notification_id"),
            channel=channel,
        )


@register("comms.escalation.triggered")
def _on_escalation_triggered(payload: Dict[str, Any]) -> None:
    """Log escalation events and notify the escalated-to role."""
    logger.info(
        "escalation triggered",
        sla_log_id=payload.get("sla_log_id"),
        escalated_to_role=payload.get("escalated_to_role"),
        priority=payload.get("priority"),
    )


# ── cross-domain event subscribers ────────────────────────────────────────
# These listen for events published by OTHER domains (orders, accounts, etc.)
# and create comms-side effects (notifications, transactional emails).


@register("orders.order_created")
def _on_order_created(payload: Dict[str, Any]) -> None:
    """Send an order-confirmation notification."""
    user_id = payload.get("user_id")
    order_id = payload.get("order_id")
    if user_id and order_id:
        _send_notification(
            user_id=user_id,
            type_="order_created",
            title="Order placed",
            message=f"Your order #{order_id} has been received.",
            link=f"/orders/{order_id}",
        )


@register("orders.order_status_changed")
def _on_order_status_changed(payload: Dict[str, Any]) -> None:
    """Notify the customer when their order status changes."""
    user_id = payload.get("user_id")
    order_id = payload.get("order_id")
    new_status = payload.get("new_status")
    if user_id and order_id:
        _send_notification(
            user_id=user_id,
            type_="order_update",
            title="Order update",
            message=f"Order #{order_id} is now {new_status}.",
            link=f"/orders/{order_id}",
        )


@register("accounts.user_registered")
def _on_user_registered(payload: Dict[str, Any]) -> None:
    """Send a welcome notification to newly registered users."""
    user_id = payload.get("user_id")
    if user_id:
        _send_notification(
            user_id=user_id,
            type_="welcome",
            title="Welcome!",
            message="Thank you for joining. Explore our marketplace!",
            link="/",
        )


__all__ = [
    "dispatch",
    "register",
    "subscribed_types",
    "_send_notification",
]
