"""Notification Gateway — unified messaging API for ALL domains.

Any module can call this gateway to send messages to any recipient.
Admin/Employee configure the rules for WHEN and WHERE messages go.

Usage:
    from domains.comms.services.notification_gateway import notify
    
    # Send to customer
    notify(
        event="order.confirmed",
        recipient_type="customer",
        recipient_id=123,
        channel="sms",
        data={"order_id": "ORD-001", "total": "AED 150"}
    )
    
    # Send to supplier
    notify(
        event="order.new",
        recipient_type="supplier",
        recipient_id=456,
        channel="whatsapp",
        data={"order_id": "ORD-001", "items": 3}
    )
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from infrastructure.utils.phone_utils import normalize_phone_number
from infrastructure.utils.message_templates import render_template
from providers.comms.sms import send_sms, SMS_MODE
from providers.comms.whatsapp_selfhosted import send_whatsapp_message, WHATSAPP_MODE

logger = logging.getLogger(__name__)


class NotificationResult:
    """Result of a notification send attempt."""

    def __init__(
        self,
        success: bool,
        channel: str,
        recipient_type: str,
        recipient_id: int,
        event: str,
        to: str | None = None,
        preview: bool = False,
        error: str | None = None,
        provider_response: dict | None = None,
    ):
        self.success = success
        self.channel = channel
        self.recipient_type = recipient_type
        self.recipient_id = recipient_id
        self.event = event
        self.to = to
        self.preview = preview
        self.error = error
        self.provider_response = provider_response or {}
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "channel": self.channel,
            "recipient_type": self.recipient_type,
            "recipient_id": self.recipient_id,
            "event": self.event,
            "to": self.to,
            "preview": self.preview,
            "error": self.error,
            "timestamp": self.timestamp,
        }


def notify(
    db: Session,
    event: str,
    recipient_type: str,
    recipient_id: int,
    channel: str = "sms",
    template_id: str | None = None,
    data: dict[str, Any] | None = None,
    force: bool = False,
) -> NotificationResult:
    """Send a notification to a specific recipient.

    This is the single entry point for ALL module notifications.

    Args:
        db: Database session
        event: Event identifier (e.g., "order.confirmed", "payment.success")
        recipient_type: "customer", "supplier", "logistics", "employee", "admin"
        recipient_id: ID of the recipient in their respective table
        channel: "sms" or "whatsapp"
        template_id: Template to use (auto-detected from event if not provided)
        data: Template variables
        force: Skip rule checking (for manual sends)

    Returns:
        NotificationResult with delivery status
    """
    data = data or {}

    # Check notification rules (unless forced)
    if not force:
        rule_check = _check_notification_rules(db, event, recipient_type, channel)
        if not rule_check["allowed"]:
            logger.info(
                "Notification suppressed by rule: event=%s recipient=%s channel=%s",
                event, recipient_type, channel,
            )
            return NotificationResult(
                success=False,
                channel=channel,
                recipient_type=recipient_type,
                recipient_id=recipient_id,
                event=event,
                error="suppressed_by_rule",
            )

    # Get recipient phone number
    phone = _get_recipient_phone(db, recipient_type, recipient_id)
    if not phone:
        logger.warning(
            "No phone number for %s id=%d, event=%s",
            recipient_type, recipient_id, event,
        )
        return NotificationResult(
            success=False,
            channel=channel,
            recipient_type=recipient_type,
            recipient_id=recipient_id,
            event=event,
            error="no_phone_number",
        )

    # Normalize phone
    e164 = normalize_phone_number(phone)
    if not e164:
        return NotificationResult(
            success=False,
            channel=channel,
            recipient_type=recipient_type,
            recipient_id=recipient_id,
            event=event,
            to=phone,
            error="invalid_phone",
        )

    # Determine template
    if not template_id:
        template_id = _resolve_template(event, channel)

    # Render message
    try:
        message = render_template(template_id, **data) if template_id else data.get("message", "")
    except ValueError:
        message = data.get("message", "")

    if not message:
        return NotificationResult(
            success=False,
            channel=channel,
            recipient_type=recipient_type,
            recipient_id=recipient_id,
            event=event,
            to=e164,
            error="no_message_content",
        )

    # Send via provider
    if channel == "sms":
        return _send_sms(e164, message, recipient_type, recipient_id, event)
    elif channel == "whatsapp":
        return _send_whatsapp(e164, message, recipient_type, recipient_id, event)
    else:
        return NotificationResult(
            success=False,
            channel=channel,
            recipient_type=recipient_type,
            recipient_id=recipient_id,
            event=event,
            to=e164,
            error=f"unknown_channel: {channel}",
        )


def notify_bulk(
    db: Session,
    event: str,
    recipient_type: str,
    recipient_ids: list[int],
    channel: str = "sms",
    data: dict[str, Any] | None = None,
    force: bool = False,
) -> list[NotificationResult]:
    """Send notifications to multiple recipients.

    Args:
        db: Database session
        event: Event identifier
        recipient_type: Type of recipients
        recipient_ids: List of recipient IDs
        channel: sms or whatsapp
        data: Template variables
        force: Skip rule checking

    Returns:
        List of NotificationResult for each recipient
    """
    results = []
    for recipient_id in recipient_ids:
        result = notify(
            db=db,
            event=event,
            recipient_type=recipient_type,
            recipient_id=recipient_id,
            channel=channel,
            data=data,
            force=force,
        )
        results.append(result)
    return results


def _get_recipient_phone(db: Session, recipient_type: str, recipient_id: int) -> str | None:
    """Get phone number for a recipient by type and id."""
    try:
        if recipient_type == "customer":
            from domains.accounts.ports import User
            user = db.query(User).filter(User.id == recipient_id).first()
            return user.phone if user else None

        elif recipient_type == "supplier":
            from domains.suppliers.models.suppliers import Supplier
            supplier = db.query(Supplier).filter(Supplier.id == recipient_id).first()
            return supplier.phone if supplier else None

        elif recipient_type == "logistics":
            from domains.logistics.ports import LogisticsPartner
            partner = db.query(LogisticsPartner).filter(LogisticsPartner.id == recipient_id).first()
            return partner.phone if partner else None

        elif recipient_type == "employee":
            from domains.hr.ports import Employee
            employee = db.query(Employee).filter(Employee.id == recipient_id).first()
            return employee.phone if employee else None

        elif recipient_type == "admin":
            from domains.accounts.ports import User
            user = db.query(User).filter(User.id == recipient_id).first()
            return user.phone if user else None

    except Exception as exc:
        logger.error("Failed to get phone for %s id=%d: %s", recipient_type, recipient_id, exc)
        return None

    return None


def _resolve_template(event: str, channel: str) -> str:
    """Resolve template ID from event and channel."""
    # Event-to-template mapping
    event_templates = {
        # Orders
        "order.confirmed": "order_confirmed",
        "order.shipped": "order_shipped",
        "order.delivered": "order_delivered",
        "order.cancelled": "order_cancelled",
        # Payments
        "payment.success": "payment_success",
        "payment.failed": "payment_failed",
        "payment.refund": "payment_refund",
        # Delivery
        "delivery.assigned": "delivery_assigned",
        "delivery.picked_up": "delivery_picked_up",
        "delivery.in_transit": "delivery_in_transit",
        "delivery.completed": "delivery_completed",
        # Payouts
        "payout.initiated": "payout_initiated",
        "payout.completed": "payout_completed",
        # Promotions
        "promotion.flash_sale": "flash_sale",
        "promotion.new_product": "product_launch",
        "promotion.general": "promo",
        # Account
        "account.welcome": "welcome",
        "account.otp": "otp",
    }

    base_template = event_templates.get(event, event.replace(".", "_"))
    return f"{base_template}_{channel}"


def _check_notification_rules(
    db: Session,
    event: str,
    recipient_type: str,
    channel: str,
) -> dict:
    """Check if notification is allowed by admin-configured rules."""
    # TODO: Implement rule checking from database
    # For now, allow all notifications
    return {"allowed": True, "rule": None}


def _send_sms(
    to: str,
    message: str,
    recipient_type: str,
    recipient_id: int,
    event: str,
) -> NotificationResult:
    """Send SMS via provider."""
    # Truncate if needed
    if len(message) > 160:
        message = message[:157] + "..."

    result = send_sms(to, message)

    if result.get("sent"):
        return NotificationResult(
            success=True,
            channel="sms",
            recipient_type=recipient_type,
            recipient_id=recipient_id,
            event=event,
            to=to,
            provider_response=result,
        )
    elif result.get("preview"):
        return NotificationResult(
            success=False,
            channel="sms",
            recipient_type=recipient_type,
            recipient_id=recipient_id,
            event=event,
            to=to,
            preview=True,
            error=f"preview_mode ({SMS_MODE})",
            provider_response=result,
        )
    else:
        return NotificationResult(
            success=False,
            channel="sms",
            recipient_type=recipient_type,
            recipient_id=recipient_id,
            event=event,
            to=to,
            error=result.get("error", "sms_failed"),
            provider_response=result,
        )


def _send_whatsapp(
    to: str,
    message: str,
    recipient_type: str,
    recipient_id: int,
    event: str,
) -> NotificationResult:
    """Send WhatsApp via provider."""
    result = send_whatsapp_message(to, message)

    if result.get("delivered"):
        return NotificationResult(
            success=True,
            channel="whatsapp",
            recipient_type=recipient_type,
            recipient_id=recipient_id,
            event=event,
            to=to,
            provider_response=result,
        )
    elif result.get("preview"):
        return NotificationResult(
            success=False,
            channel="whatsapp",
            recipient_type=recipient_type,
            recipient_id=recipient_id,
            event=event,
            to=to,
            preview=True,
            error=f"preview_mode ({WHATSAPP_MODE})",
            provider_response=result,
        )
    else:
        return NotificationResult(
            success=False,
            channel="whatsapp",
            recipient_type=recipient_type,
            recipient_id=recipient_id,
            event=event,
            to=to,
            error=result.get("error", "whatsapp_failed"),
            provider_response=result,
        )


__all__ = [
    "NotificationResult",
    "notify",
    "notify_bulk",
]
