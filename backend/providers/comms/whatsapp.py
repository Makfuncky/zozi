"""WhatsApp messages provider.

Vendor/protocol code for WhatsApp delivery is encapsulated here so the comms
*service* layer stays free of third-party client details. The service layer is
responsible for config resolution (env/DB) and event recording, then calls
:func:`send_whatsapp_message` with the already-resolved transport descriptor.

Delivery uses the Twilio WhatsApp Cloud API when the ``twilio`` SDK is
available; otherwise it degrades to a console preview so local/dev boots never
fail on a missing optional dependency.
"""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)

try:
    from providers.comms.twilio import (
        TWILIO_AVAILABLE,
        create_twilio_client,
    )

    _HAVE_TWILIO = TWILIO_AVAILABLE
except Exception as exc:  # pragma: no cover - defensive
    logger.warning("whatsapp_provider_twilio_unavailable: %s", exc)
    _HAVE_TWILIO = False

    def create_twilio_client(*_a, **_k):  # type: ignore
        return None


def _normalize_wa(number: str) -> str:
    """Twilio expects the ``whatsapp:`` prefix on E.164 numbers."""
    number = (number or "").strip()
    if number.startswith("whatsapp:"):
        return number
    return f"whatsapp:{number}"


def send_whatsapp_message(
    to: str,
    body: str,
    *,
    from_number: str,
    account_sid: str = "",
    auth_token: str = "",
    preview: bool = False,
) -> dict:
    """Send a WhatsApp text message.

    Returns a small result descriptor consumed by the service layer. When the
    Twilio SDK is unavailable or ``preview`` is set, the message is only logged
    (console preview mode) and ``delivered`` is ``False``.
    """
    to_wa = _normalize_wa(to)
    from_wa = _normalize_wa(from_number)

    if preview or not _HAVE_TWILIO or not account_sid or not auth_token:
        logger.warning(
            "[DEV WHATSAPP] From: %s | To: %s\n%s",
            from_wa, to_wa, body,
        )
        return {"delivered": False, "channel": "whatsapp", "preview": True, "to": to_wa}

    client = create_twilio_client(account_sid, auth_token)
    if client is None:
        logger.warning("[DEV WHATSAPP] Twilio client unavailable; preview only")
        return {"delivered": False, "channel": "whatsapp", "preview": True, "to": to_wa}

    message = client.messages.create(
        to=to_wa,
        from_=from_wa,
        body=body,
    )
    logger.info("WhatsApp message sent to %s (sid=%s)", to_wa, getattr(message, "sid", None))
    return {
        "delivered": True,
        "channel": "whatsapp",
        "preview": False,
        "to": to_wa,
        "sid": getattr(message, "sid", None),
    }


__all__ = ["WHATSAPP_AVAILABLE", "send_whatsapp_message"]

# Expose availability for call sites that branch on optional deps.
WHATSAPP_AVAILABLE = _HAVE_TWILIO
