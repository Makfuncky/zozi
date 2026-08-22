"""Tests for the WhatsApp provider + service (P4)."""
import importlib
import os

import pytest


def test_whatsapp_provider_importable():
    from providers.comms.whatsapp import send_whatsapp_message, WHATSAPP_AVAILABLE
    assert callable(send_whatsapp_message)


def test_send_whatsapp_preview_mode_without_credentials():
    # Ensure no creds leak from the environment in CI.
    os.environ.pop("WHATSAPP_ACCOUNT_SID", None)
    os.environ.pop("WHATSAPP_AUTH_TOKEN", None)
    os.environ.pop("WHATSAPP_FROM_NUMBER", None)
    from domains.comms.services.whatsapp_service import send_message

    result = send_message("+15551234567", "Hello from ZOZI")
    assert result["channel"] == "whatsapp"
    assert result["preview"] is True
    assert result["delivered"] is False


def test_send_whatsapp_normalizes_numbers():
    os.environ.pop("WHATSAPP_ACCOUNT_SID", None)
    os.environ.pop("WHATSAPP_AUTH_TOKEN", None)
    os.environ.pop("WHATSAPP_FROM_NUMBER", None)
    from domains.comms.services.whatsapp_service import send_message

    # Provider only ensures the "whatsapp:" prefix; callers supply E.164 (+).
    result = send_message("+15551234567", "hi", from_number="+15557654321")
    assert result["to"] == "whatsapp:+15551234567"


def test_comms_package_exports_whatsapp():
    import providers.comms as comms

    assert hasattr(comms, "send_whatsapp_message")
    assert hasattr(comms, "WHATSAPP_AVAILABLE")
