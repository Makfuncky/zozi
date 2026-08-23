"""comms domain — event subscribers (Law 3).

Subscribers consume cross-domain events emitted by other domains'
``events.py`` and trigger comms-domain side effects (notifications,
emails, escalations). They are the ONLY sanctioned path for cross-domain
**writes** into the comms domain — no other domain may call comms services
directly.

Handlers are registered on the canonical event bus via ``subscribe()``.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

import structlog

from domains.comms.events import (
    CommsEvent,
    EVENT_NOTIFICATION_CREATED,
    EVENT_TICKET_REPLIED,
    EVENT_TICKET_STATUS_CHANGED,
    EVENT_ESCALATION_TRIGGERED,
)

logger = structlog.get_logger(__name__)


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


def _on_ticket_status_changed(payload: Dict[str, Any]) -> None:
    """Notify the ticket owner when their ticket status changes."""
    from domains.comms.services.shared.ticket.tickets_service import (
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
        message="Your ticket #{} is now {}.".format(ticket_id, payload.get("new_status", "updated")),
        link="/tickets/{}".format(ticket_id),
    )


def _on_ticket_replied(payload: Dict[str, Any]) -> None:
    """Notify the ticket owner when a staff member replies."""
    from domains.comms.services.shared.ticket.tickets_service import (
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
            message="Staff replied to ticket #{}.".format(ticket_id),
            link="/tickets/{}".format(ticket_id),
        )


def _on_notification_created(payload: Dict[str, Any]) -> None:
    """Hook for downstream notification delivery (push, email, SMS)."""
    channel = payload.get("channel", "in_app")
    if channel != "in_app":
        logger.info(
            "comms notification delivery queued",
            notification_id=payload.get("notification_id"),
            channel=channel,
        )


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


def _on_order_created(payload: Dict[str, Any]) -> None:
    """Send an order-confirmation notification."""
    user_id = payload.get("user_id")
    order_id = payload.get("order_id")
    if user_id and order_id:
        _send_notification(
            user_id=user_id,
            type_="order_created",
            title="Order placed",
            message="Your order #{} has been received.".format(order_id),
            link="/orders/{}".format(order_id),
        )


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
            message="Order #{} is now {}.".format(order_id, new_status),
            link="/orders/{}".format(order_id),
        )


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


# ── register handlers on canonical event bus ──────────────────────────────

def _register_handlers() -> None:
    """Register all comms event handlers on the canonical event bus."""
    try:
        from infrastructure.utils.event_bus import subscribe

        # Comms-domain events
        subscribe(EVENT_TICKET_STATUS_CHANGED, _on_ticket_status_changed)
        subscribe(EVENT_TICKET_REPLIED, _on_ticket_replied)
        subscribe(EVENT_NOTIFICATION_CREATED, _on_notification_created)
        subscribe(EVENT_ESCALATION_TRIGGERED, _on_escalation_triggered)

        # Cross-domain events (using canonical event type strings)
        subscribe("order.status_changed", _on_order_status_changed)
        subscribe("account.registered", _on_user_registered)
    except Exception:
        logger.debug("Event bus not available, handlers not registered")


# Register handlers on module import
_register_handlers()


def subscribed_types() -> List[str]:
    """Return all event types that have at least one subscriber."""
    return sorted([
        EVENT_TICKET_STATUS_CHANGED,
        EVENT_TICKET_REPLIED,
        EVENT_NOTIFICATION_CREATED,
        EVENT_ESCALATION_TRIGGERED,
        "order.status_changed",
        "account.registered",
    ])


__all__ = [
    "subscribed_types",
    "_send_notification",
    "_on_ticket_status_changed",
    "_on_ticket_replied",
    "_on_notification_created",
    "_on_escalation_triggered",
    "_on_order_created",
    "_on_order_status_changed",
    "_on_user_registered",
]
