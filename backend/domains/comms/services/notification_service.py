"""Notification service layer — unified interface for SMS and WhatsApp.

Provides a single entry point for all notification delivery with:
- Channel routing (SMS or WhatsApp)
- Phone number validation
- Template rendering
- Delivery tracking
- Rate limiting
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from infrastructure.utils.phone_utils import normalize_phone_number, validate_phone_number
from domains.comms.services.templates import render as render_locale_template
from infrastructure.utils.message_templates import render_template, get_channel
from providers.comms.sms import send_sms, SMS_MODE
from providers.comms.whatsapp_selfhosted import send_whatsapp_message, WHATSAPP_MODE

logger = logging.getLogger(__name__)


class NotificationResult:
    """Result of a notification send attempt."""

    def __init__(
        self,
        success: bool,
        channel: str,
        to: str,
        template_id: str | None = None,
        preview: bool = False,
        error: str | None = None,
        provider_response: dict | None = None,
    ):
        self.success = success
        self.channel = channel
        self.to = to
        self.template_id = template_id
        self.preview = preview
        self.error = error
        self.provider_response = provider_response or {}
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "channel": self.channel,
            "to": self.to,
            "template_id": self.template_id,
            "preview": self.preview,
            "error": self.error,
            "provider_response": self.provider_response,
            "timestamp": self.timestamp,
        }


def send_notification(
    to: str,
    template_id: str | None = None,
    channel: str | None = None,
    body: str | None = None,
    country_code: str | None = None,
    **template_vars: Any,
) -> NotificationResult:
    """Send a notification via SMS or WhatsApp.

    Args:
        to: Phone number (any format)
        template_id: Template identifier (from message_templates.py)
        channel: "sms" or "whatsapp" (auto-detected from template if not specified)
        body: Raw message body (used if template_id not provided)
        country_code: ISO country code for phone validation
        **template_vars: Variables for template substitution

    Returns:
        NotificationResult with delivery status
    """
    # Validate and normalize phone number
    e164 = normalize_phone_number(to, country_code)
    if not e164:
        return NotificationResult(
            success=False,
            channel=channel or "unknown",
            to=to,
            template_id=template_id,
            error="invalid_phone_number",
        )

    validation = validate_phone_number(to, country_code)
    if not validation["valid"]:
        logger.warning("Phone validation failed for %s: %s", to, validation.get("error"))

    # Determine channel
    if not channel and template_id:
        channel = get_channel(template_id)
    if not channel:
        channel = "sms"  # Default to SMS

    # Render message body (locale-aware when country_code is AE/SA).
    if template_id:
        try:
            if country_code:
                body = render_locale_template(
                    template_id, country_code=country_code, **template_vars
                )
            else:
                body = render_template(template_id, **template_vars)
        except ValueError as exc:
            return NotificationResult(
                success=False,
                channel=channel,
                to=e164,
                template_id=template_id,
                error=f"template_error: {exc}",
            )
    elif not body:
        return NotificationResult(
            success=False,
            channel=channel,
            to=e164,
            template_id=template_id,
            error="no_content",
        )

    # Truncate SMS to 160 chars if needed
    if channel == "sms" and len(body) > 160:
        logger.warning("SMS message exceeds 160 chars (%d), truncating", len(body))
        body = body[:157] + "..."

    # Send via appropriate provider
    if channel == "sms":
        return _send_sms_notification(e164, body, template_id)
    elif channel == "whatsapp":
        return _send_whatsapp_notification(e164, body, template_id)
    else:
        return NotificationResult(
            success=False,
            channel=channel,
            to=e164,
            template_id=template_id,
            error=f"unknown_channel: {channel}",
        )


def _send_sms_notification(
    to: str,
    body: str,
    template_id: str | None = None,
) -> NotificationResult:
    """Send SMS notification."""
    result = send_sms(to, body)

    if result.get("sent"):
        return NotificationResult(
            success=True,
            channel="sms",
            to=to,
            template_id=template_id,
            provider_response=result,
        )
    elif result.get("preview"):
        return NotificationResult(
            success=False,
            channel="sms",
            to=to,
            template_id=template_id,
            preview=True,
            error=f"preview_mode ({SMS_MODE})",
            provider_response=result,
        )
    else:
        return NotificationResult(
            success=False,
            channel="sms",
            to=to,
            template_id=template_id,
            error=result.get("error", "sms_failed"),
            provider_response=result,
        )


def _send_whatsapp_notification(
    to: str,
    body: str,
    template_id: str | None = None,
) -> NotificationResult:
    """Send WhatsApp notification."""
    result = send_whatsapp_message(to, body)

    if result.get("delivered"):
        return NotificationResult(
            success=True,
            channel="whatsapp",
            to=to,
            template_id=template_id,
            provider_response=result,
        )
    elif result.get("preview"):
        return NotificationResult(
            success=False,
            channel="whatsapp",
            to=to,
            template_id=template_id,
            preview=True,
            error=f"preview_mode ({WHATSAPP_MODE})",
            provider_response=result,
        )
    else:
        return NotificationResult(
            success=False,
            channel="whatsapp",
            to=to,
            template_id=template_id,
            error=result.get("error", "whatsapp_failed"),
            provider_response=result,
        )


def send_otp(
    to: str,
    code: str,
    channel: str = "sms",
    country_code: str | None = None,
) -> NotificationResult:
    """Send OTP verification code.

    Args:
        to: Phone number
        code: 6-digit OTP code
        channel: "sms" or "whatsapp"
        country_code: ISO country code

    Returns:
        NotificationResult
    """
    template_id = f"otp_{channel}"
    return send_notification(
        to=to,
        template_id=template_id,
        channel=channel,
        code=code,
        country_code=country_code,
    )


def get_status() -> dict:
    """Get current status of notification providers."""
    return {
        "sms": {
            "mode": SMS_MODE,
            "provider": _get_sms_provider_name(),
        },
        "whatsapp": {
            "mode": WHATSAPP_MODE,
            "provider": _get_whatsapp_provider_name(),
        },
    }


def _get_sms_provider_name() -> str:
    from providers.comms.sms import SMS_HTTP_PROVIDER
    if SMS_MODE == "dev":
        return "dev_preview"
    elif SMS_MODE == "gsm":
        return "gsm_modem"
    elif SMS_MODE == "http":
        return SMS_HTTP_PROVIDER
    return "unknown"


def _get_whatsapp_provider_name() -> str:
    if WHATSAPP_MODE == "dev":
        return "dev_preview"
    elif WHATSAPP_MODE == "web":
        return "whatsapp_web"
    elif WHATSAPP_MODE == "business_api":
        return "meta_business_api"
    return "unknown"


__all__ = [
    "NotificationResult",
    "send_notification",
    "send_otp",
    "get_status",
    "mark_notification_as_read",
]


def mark_notification_as_read(db, notification) -> None:
    """Mark a notification as read. Service layer for Law 2 compliance."""
    notification.is_read = True
    db.commit()
