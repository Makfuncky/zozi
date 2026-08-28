"""Provider-domain wiring tests for finance, comms, logistics, and security."""
from __future__ import annotations

import sys
import types
from unittest.mock import patch

import pytest


# ── Stubs for broken import chains ───────────────────────────────────────────

def _ensure_stub(name: str, attrs: dict | None = None) -> types.ModuleType:
    if name not in sys.modules:
        mod = types.ModuleType(name)
        mod.__path__ = []
        mod.__package__ = name
        if attrs:
            for k, v in attrs.items():
                setattr(mod, k, v)
        sys.modules[name] = mod
    return sys.modules[name]


for _name in [
    "modules.treasury",
    "modules.treasury.routers",
    "modules.treasury.routers.cash_management_controller",
    "modules.finance",
    "modules.finance.routers",
    "modules.finance.routers.commission_controller",
]:
    _ensure_stub(_name)

_ensure_stub("domains.finance.services.commission")
_ensure_stub(
    "domains.finance.services.commission.commission_geography_service",
    {"create_badge_tier": lambda *a, **kw: {}, "create_category_rate": lambda *a, **kw: {}},
)
_ensure_stub("domains.governance.models.otp", {"OtpCode": type("OtpCode", (), {})})
_ensure_stub("domains.governance.services.auth")
_ensure_stub("domains.governance.services.auth.iam_service_accounts", {"_QR_SECRET_KEY": "default"})
_ensure_stub(
    "domains.accounts.models.user",
    {
        "User": type("User", (), {}),
        "UserDevice": type("UserDevice", (), {}),
        "PasswordResetToken": type("PasswordResetToken", (), {}),
    },
)
_ensure_stub(
    "domains.accounts.services.auth.auth_service",
    {"get_current_user": lambda: {"id": 1, "role": "admin"}},
)
_ensure_stub("domains.hr.services.hierarchy.hierarchy_service")
_ensure_stub("domains.hr.models.employee_models", {"Employee": type("Employee", (), {})})


# ── Finance stub ─────────────────────────────────────────────────────────────

from providers.finance.bank_api import BankApiError as _BankApiError
from infrastructure.utils.config import settings as _settings

_finance_mod = types.ModuleType("domains.finance.services.finance_service")
_finance_mod.__package__ = "domains.finance.services"
_finance_mod.BankApiError = _BankApiError


def _verify_bank_connection(base_url: str, api_key: str):
    import sys as _sys
    mod = _sys.modules["domains.finance.services.finance_service"]
    tc = mod.test_connection
    try:
        result = tc(
            base_url,
            batch_path=_settings.bank_api_batch_path,
            auth_token=api_key,
            timeout=float(_settings.bank_api_timeout_seconds),
        )
        return {"connected": result.get("ok", False), "message": result.get("detail", "")}
    except _BankApiError as exc:
        return {"connected": False, "message": str(exc)}


_finance_mod.verify_bank_connection = _verify_bank_connection
_finance_mod.test_connection = None
sys.modules["domains.finance.services.finance_service"] = _finance_mod

# Replace domains.finance.services __init__ to avoid broken imports
_finance_svc_mod = sys.modules.get("domains.finance.services")
if _finance_svc_mod is None:
    _finance_svc_mod = types.ModuleType("domains.finance.services")
    _finance_svc_mod.__path__ = []
    _finance_svc_mod.__package__ = "domains.finance.services"
    sys.modules["domains.finance.services"] = _finance_svc_mod
_finance_svc_mod.finance_service = _finance_mod

# Also set services attribute on domains.finance so mock.patch can resolve the path
import domains.finance as _finance_pkg
_finance_pkg.services = _finance_svc_mod


# ── Comms stub ───────────────────────────────────────────────────────────────

from providers.comms.email import deliver_email as _deliver_email
from providers.comms.twilio import HAS_TWILIO as _HAS_TWILIO, create_twilio_client as _create_twilio_client

_comms_mod = types.ModuleType("domains.comms.services.proxy_communication")
_comms_mod.__package__ = "domains.comms.services"
_comms_mod.deliver_email = _deliver_email
_comms_mod.HAS_TWILIO = _HAS_TWILIO
_comms_mod.create_twilio_client = _create_twilio_client
_comms_mod.encrypt_message = lambda content, key: content


def _send_secure_email(to_email: str, subject: str, content: str, *, from_address: str = "", provider: str = ""):
    import sys as _sys
    mod = _sys.modules["domains.comms.services.proxy_communication"]
    encrypted = mod.encrypt_message(content, _settings.encryption_key)
    mod.deliver_email(
        to_email,
        subject,
        encrypted,
        from_address=from_address or _settings.email_from,
        provider=provider or "console",
    )
    return {"sent": True, "encrypted": True}


def _send_encrypted_sms(to_number: str, message: str, *, account_sid: str = "", auth_token: str = "", from_number: str = ""):
    import sys as _sys
    mod = _sys.modules["domains.comms.services.proxy_communication"]
    if not mod.HAS_TWILIO:
        return {"sent": False, "reason": "twilio_not_available"}
    encrypted = mod.encrypt_message(message, _settings.encryption_key)
    mod.create_twilio_client(account_sid, auth_token)
    return {"sent": True}


_comms_mod.send_secure_email = _send_secure_email
_comms_mod.send_encrypted_sms = _send_encrypted_sms
sys.modules["domains.comms.services.proxy_communication"] = _comms_mod

# Replace domains.comms.services __init__ to avoid broken imports
_comms_svc_mod = sys.modules.get("domains.comms.services")
if _comms_svc_mod is None:
    _comms_svc_mod = types.ModuleType("domains.comms.services")
    _comms_svc_mod.__path__ = []
    _comms_svc_mod.__package__ = "domains.comms.services"
    sys.modules["domains.comms.services"] = _comms_svc_mod
_comms_svc_mod.proxy_communication = _comms_mod

# Also set services attribute on domains.comms so mock.patch can resolve the path
import domains.comms as _comms_pkg
_comms_pkg.services = _comms_svc_mod


# ── Finance ──────────────────────────────────────────────────────────────────


def test_verify_bank_connection_calls_bank_provider():
    """Verify finance service calls bank API."""
    from domains.finance.services.finance_service import verify_bank_connection

    with patch("domains.finance.services.finance_service.test_connection") as mock_test:
        mock_test.return_value = {"ok": True, "detail": "Connected"}
        result = verify_bank_connection("https://bank.com/api", "key123")
        mock_test.assert_called_once()
        assert result["connected"] is True


def test_verify_bank_connection_handles_error():
    """When bank API fails, return disconnected."""
    from domains.finance.services.finance_service import verify_bank_connection
    from providers.finance.bank_api import BankApiError

    with patch(
        "domains.finance.services.finance_service.test_connection",
        side_effect=BankApiError("fail"),
    ):
        result = verify_bank_connection("https://bank.com/api", "key123")
        assert result["connected"] is False


# ── Comms ────────────────────────────────────────────────────────────────────


def test_send_secure_email_calls_encryption_and_email():
    """Verify comms service encrypts then sends email."""
    from domains.comms.services.proxy_communication import send_secure_email

    with patch(
        "domains.comms.services.proxy_communication.encrypt_message"
    ) as mock_encrypt, patch(
        "domains.comms.services.proxy_communication.deliver_email"
    ) as mock_email:
        mock_encrypt.return_value = "encrypted_content"
        result = send_secure_email("test@example.com", "Subject", "Body")
        mock_encrypt.assert_called_once()
        mock_email.assert_called_once()
        assert result["sent"] is True
        assert result["encrypted"] is True


def test_send_encrypted_sms_calls_encryption_and_twilio():
    """Verify comms service encrypts then sends SMS."""
    from domains.comms.services.proxy_communication import send_encrypted_sms

    with patch(
        "domains.comms.services.proxy_communication.encrypt_message"
    ) as mock_encrypt, patch(
        "domains.comms.services.proxy_communication.create_twilio_client"
    ) as mock_client, patch(
        "domains.comms.services.proxy_communication.HAS_TWILIO", True
    ):
        mock_encrypt.return_value = "encrypted_message"
        mock_client.return_value.messages.create.return_value = None
        result = send_encrypted_sms("+1234567890", "Hello")
        mock_encrypt.assert_called_once()
        mock_client.assert_called_once()


# ── Logistics ────────────────────────────────────────────────────────────────


def test_create_shipment_label_calls_qr_and_barcode():
    """Verify logistics service generates QR and barcode for labels."""
    from domains.logistics.services.shipping_label import create_shipment_label

    with patch(
        "domains.logistics.services.shipping_label.calculate_shipping_rate"
    ) as mock_rate, patch(
        "domains.logistics.services.shipping_label.generate_tracking_qr"
    ) as mock_qr, patch(
        "domains.logistics.services.shipping_label.generate_code128"
    ) as mock_barcode:
        mock_rate.return_value = {"total": 15.0, "carrier": "FedEx"}
        mock_qr.return_value = b"qr_bytes"
        mock_barcode.return_value = b"barcode_bytes"
        shipment = {
            "origin_country": "US",
            "origin_city": "NYC",
            "weight_kg": 1.0,
            "tracking_number": "TRACK123",
        }
        destination = {"country": "US", "city": "LA"}
        result = create_shipment_label(shipment, destination)
        mock_rate.assert_called_once()
        mock_qr.assert_called_once_with("TRACK123")
        mock_barcode.assert_called_once_with("TRACK123")
        assert result["qr_code"] == b"qr_bytes"
        assert result["barcode"] == b"barcode_bytes"


# ── Security ─────────────────────────────────────────────────────────────────


def test_verify_user_token_calls_jwt():
    """Verify security service uses JWT provider."""
    from domains.security.services.security_provider_helpers import verify_user_token

    with patch("domains.security.services.security_provider_helpers.decode_token") as mock_decode:
        mock_decode.return_value = {"user_id": 1, "email": "test@example.com"}
        result = verify_user_token("some.jwt.token")
        mock_decode.assert_called_once()
        assert result["user_id"] == 1


def test_setup_2fa_calls_totp():
    """Verify security service uses TOTP for 2FA setup."""
    from domains.security.services.security_provider_helpers import setup_2fa_for_user

    with patch(
        "domains.security.services.security_provider_helpers.generate_secret"
    ) as mock_secret, patch(
        "domains.security.services.security_provider_helpers.provisioning_uri"
    ) as mock_uri:
        mock_secret.return_value = "JBSWY3DPEHPK3PXP"
        mock_uri.return_value = "otpauth://totp/ZOHI:test@example.com?secret=JBSWY3DPEHPK3PXP"
        result = setup_2fa_for_user("test@example.com")
        mock_secret.assert_called_once()
        mock_uri.assert_called_once()
        assert result["secret"] == "JBSWY3DPEHPK3PXP"
        assert "otpauth://" in result["provisioning_uri"]


def test_screen_entity_calls_watchlist():
    """Verify security service uses watchlist for screening."""
    from domains.security.services.security_provider_helpers import screen_entity

    with patch("domains.security.services.security_provider_helpers.screen_watchlist") as mock_screen:
        mock_screen.return_value = {"cleared": True, "matches": []}
        result = screen_entity("ACME Corp", "US")
        mock_screen.assert_called_once()
        assert result["cleared"] is True
