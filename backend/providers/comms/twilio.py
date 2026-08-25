"""Twilio communication provider.

Vendor SDK (``twilio``) is encapsulated here so the comms service layer stays
free of third-party client code. ``services`` orchestrates through
:func:`create_twilio_client` and :data:`TwilioRestException`.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

try:
    from twilio.rest import Client as _TwilioClient
    from twilio.base.exceptions import TwilioRestException as _TwilioRestException

    HAS_TWILIO = True
except ImportError as exc:  # pragma: no cover - optional dependency
    logger.warning("optional_dependency_unavailable: %s", exc)
    _TwilioClient = None
    _TwilioRestException = Exception
    HAS_TWILIO = False

# Re-export the resolved exception type under the public name expected by
# call sites (`from providers.comms.twilio import TwilioRestException`).
TwilioRestException = _TwilioRestException


def create_twilio_client(account_sid: str, auth_token: str):
    """Build a Twilio REST client, or ``None`` when the SDK is unavailable."""
    if not HAS_TWILIO:
        return None
    return _TwilioClient(account_sid, auth_token)


__all__ = ["HAS_TWILIO", "TwilioRestException", "create_twilio_client"]
