"""WhatsApp messaging service (SERVICES layer).

Owns WhatsApp config resolution and delegates the actual transport to
``providers.comms.whatsapp``. Controllers/routers must call this service and
never import the provider directly.
"""

from __future__ import annotations

import logging
import os
from typing import Optional

from providers.comms.whatsapp import send_whatsapp_message

logger = logging.getLogger(__name__)


def _resolve_config() -> dict:
    """Read WhatsApp transport config from the environment.

    A deployment may later back this with a DB-backed settings row; the service
    layer is the single place that knows where config comes from.
    """
    return {
        "account_sid": os.environ.get("WHATSAPP_ACCOUNT_SID", ""),
        "auth_token": os.environ.get("WHATSAPP_AUTH_TOKEN", ""),
        "from_number": os.environ.get("WHATSAPP_FROM_NUMBER", ""),
    }


def send_message(to: str, body: str, *, from_number: Optional[str] = None) -> dict:
    """Send a WhatsApp message to ``to`` with ``body``.

    Falls back to console preview when credentials are not configured so the
    app never crashes in dev.
    """
    cfg = _resolve_config()
    sender = from_number or cfg["from_number"]
    preview = not (cfg["account_sid"] and cfg["auth_token"] and sender)
    return send_whatsapp_message(
        to,
        body,
        from_number=sender,
        account_sid=cfg["account_sid"],
        auth_token=cfg["auth_token"],
        preview=preview,
    )


__all__ = ["send_message"]
