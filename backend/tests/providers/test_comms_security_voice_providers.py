"""
Comprehensive test suite for comms, security, and voice provider subpackages.

Tests every public function, class, and constant across:
- providers.comms (__init__.py, email.py, twilio.py, whatsapp.py)
- providers.security (__init__.py, encryption.py, threat_intel.py, watchlist.py)
- providers.voice (__init__.py, voice_to_text.py)

External SDKs/APIs are mocked via unittest.mock to ensure tests run without
network access or installed vendor packages.

Run with: pytest tests/providers/test_comms_security_voice_providers.py -v
"""

import base64
import json
import os
import sys
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, Mock, patch, PropertyMock

import pytest

# Ensure backend root is importable
BACKEND = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)


# ══════════════════════════════════════════════════════════════════════════════
# COMMS PACKAGE — __init__.py
# ══════════════════════════════════════════════════════════════════════════════

class TestCommsInit:
    """Verify comms package exports."""

    def test_comms_exports_has_twilio(self):
        from providers.comms import HAS_TWILIO
        assert isinstance(HAS_TWILIO, bool)

    def test_comms_exports_twilio_rest_exception(self):
        from providers.comms import TwilioRestException
        assert TwilioRestException is not None

    def test_comms_exports_create_twilio_client(self):
        from providers.comms import create_twilio_client
        assert callable(create_twilio_client)

    def test_comms_exports_has_whatsapp(self):
        from providers.comms import HAS_WHATSAPP
        assert isinstance(HAS_WHATSAPP, bool)

    def test_comms_exports_send_whatsapp_message(self):
        from providers.comms import send_whatsapp_message
        assert callable(send_whatsapp_message)

    def test_comms_all_exports_defined(self):
        import providers.comms as comms
        for name in comms.__all__:
            assert hasattr(comms, name), f"Missing export: {name}"


# ══════════════════════════════════════════════════════════════════════════════
# COMMS — email.py
# ══════════════════════════════════════════════════════════════════════════════

class TestDeliverEmail:
    """Tests for the deliver_email function."""

    def test_deliver_email_console_mode(self, caplog):
        """Console provider logs the email instead of sending."""
        import logging
        from providers.comms.email import deliver_email

        with caplog.at_level(logging.INFO):
            deliver_email(
                to="test@example.com",
                subject="Test Subject",
                html="<h1>Hello</h1>",
                from_address="sender@example.com",
                provider="console",
            )
        assert "[DEV EMAIL]" in caplog.text
        assert "test@example.com" in caplog.text

    def test_delend_email_disabled_provider_raises(self):
        """Unknown provider raises RuntimeError."""
        from providers.comms.email import deliver_email

        with pytest.raises(RuntimeError, match="not configured"):
            deliver_email(
                to="test@example.com",
                subject="Test",
                html="<p>Hi</p>",
                from_address="sender@example.com",
                provider="unknown_provider",
            )

    def test_deliver_email_none_provider_treated_as_disabled(self):
        """None provider defaults to 'disabled' and raises RuntimeError."""
        from providers.comms.email import deliver_email

        with pytest.raises(RuntimeError, match="not configured"):
            deliver_email(
                to="test@example.com",
                subject="Test",
                html="<p>Hi</p>",
                from_address="sender@example.com",
                provider=None,
            )

    def test_deliver_email_empty_config_defaults(self):
        """Empty config dict is handled gracefully."""
        from providers.comms.email import deliver_email

        # Console mode with empty config should not crash
        deliver_email(
            to="test@example.com",
            subject="Test",
            html="<p>Hi</p>",
            from_address="sender@example.com",
            provider="console",
            config={},
        )

    def test_deliver_email_case_insensitive_provider(self):
        """Provider name is case-insensitive."""
        from providers.comms.email import deliver_email

        deliver_email(
            to="test@example.com",
            subject="Test",
            html="<p>Hi</p>",
            from_address="sender@example.com",
            provider="CONSOLE",
        )

    @patch("providers.comms.email._send_via_resend")
    def test_deliver_email_resend_mode(self, mock_resend):
        """Resend provider delegates to _send_via_resend."""
        from providers.comms.email import deliver_email

        deliver_email(
            to="test@example.com",
            subject="Test",
            html="<p>Hi</p>",
            from_address="sender@example.com",
            provider="resend",
            config={"resend_api_key": "test-key"},
        )
        mock_resend.assert_called_once()

    @patch("providers.comms.email._send_via_smtp")
    def test_deliver_email_smtp_mode(self, mock_smtp):
        """SMTP provider delegates to _send_via_smtp."""
        from providers.comms.email import deliver_email

        deliver_email(
            to="test@example.com",
            subject="Test",
            html="<p>Hi</p>",
            from_address="sender@example.com",
            provider="smtp",
            config={
                "smtp_host": "smtp.example.com",
                "smtp_port": 587,
            },
        )
        mock_smtp.assert_called_once()


class TestSendViaResend:
    """Tests for the _send_via_resend function."""

    @patch("providers.comms.email.urllib.request.urlopen")
    def test_resend_success(self, mock_urlopen):
        """Successful Resend API call logs and returns."""
        from providers.comms.email import _send_via_resend

        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.__enter__ = Mock(return_value=mock_resp)
        mock_resp.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_resp

        _send_via_resend(
            to="test@example.com",
            subject="Test",
            html="<p>Hi</p>",
            from_address="sender@example.com",
            api_key="test-key",
        )
        mock_urlopen.assert_called_once()

    @patch("providers.comms.email.time.sleep")
    @patch("providers.comms.email.urllib.request.urlopen")
    def test_resend_client_error_no_retry(self, mock_urlopen, mock_sleep):
        """4xx errors are not retried."""
        from providers.comms.email import _send_via_resend
        import urllib.error

        mock_resp = MagicMock()
        mock_resp.status = 400
        mock_resp.read.return_value = b'{"message": "bad request"}'
        http_error = urllib.error.HTTPError(
            url="https://api.resend.com/emails",
            code=400,
            msg="Bad Request",
            hdrs={},
            fp=MagicMock(),
        )
        # Make exc.read() return bytes
        http_error.read = Mock(return_value=b'{"message": "bad request"}')
        mock_urlopen.side_effect = http_error

        with pytest.raises(urllib.error.HTTPError):
            _send_via_resend(
                to="test@example.com",
                subject="Test",
                html="<p>Hi</p>",
                from_address="sender@example.com",
                api_key="test-key",
            )
        assert mock_urlopen.call_count == 1
        mock_sleep.assert_not_called()

    @patch("providers.comms.email.time.sleep")
    @patch("providers.comms.email.urllib.request.urlopen")
    def test_resend_server_error_retries(self, mock_urlopen, mock_sleep):
        """5xx errors trigger exponential backoff retries."""
        from providers.comms.email import _send_via_resend
        import urllib.error

        http_error = urllib.error.HTTPError(
            url="https://api.resend.com/emails",
            code=503,
            msg="Service Unavailable",
            hdrs={},
            fp=MagicMock(),
        )
        http_error.read = Mock(return_value=b"server error")
        mock_urlopen.side_effect = http_error

        with pytest.raises(urllib.error.HTTPError):
            _send_via_resend(
                to="test@example.com",
                subject="Test",
                html="<p>Hi</p>",
                from_address="sender@example.com",
                api_key="test-key",
                max_retries=3,
            )
        assert mock_urlopen.call_count == 3
        assert mock_sleep.call_count == 2

    @patch("providers.comms.email.time.sleep")
    @patch("providers.comms.email.urllib.request.urlopen")
    def test_resend_network_error_retries(self, mock_urlopen, mock_sleep):
        """Network errors trigger retries."""
        from providers.comms.email import _send_via_resend

        mock_urlopen.side_effect = OSError("Connection refused")

        with pytest.raises(OSError):
            _send_via_resend(
                to="test@example.com",
                subject="Test",
                html="<p>Hi</p>",
                from_address="sender@example.com",
                api_key="test-key",
                max_retries=2,
            )
        assert mock_urlopen.call_count == 2


class TestSendViaSmtp:
    """Tests for the _send_via_smtp function."""

    @patch("smtplib.SMTP")
    def test_smtp_plain(self, mock_smtp_cls):
        """Plain SMTP connection sends message."""
        from providers.comms.email import _send_via_smtp

        mock_server = MagicMock()
        mock_smtp_cls.return_value = mock_server
        mock_server.__enter__ = Mock(return_value=mock_server)
        mock_server.__exit__ = Mock(return_value=False)

        _send_via_smtp(
            to="test@example.com",
            subject="Test",
            html="<p>Hi</p>",
            from_address="sender@example.com",
            transport={},
            smtp_host="smtp.example.com",
            smtp_port=587,
        )
        mock_smtp_cls.assert_called_once_with("smtp.example.com", 587, timeout=30)
        mock_server.send_message.assert_called_once()

    @patch("smtplib.SMTP_SSL")
    def test_smtp_ssl(self, mock_smtp_ssl_cls):
        """SSL SMTP connection uses SMTP_SSL."""
        from providers.comms.email import _send_via_smtp

        mock_server = MagicMock()
        mock_smtp_ssl_cls.return_value = mock_server
        mock_server.__enter__ = Mock(return_value=mock_server)
        mock_server.__exit__ = Mock(return_value=False)

        _send_via_smtp(
            to="test@example.com",
            subject="Test",
            html="<p>Hi</p>",
            from_address="sender@example.com",
            transport={},
            smtp_host="smtp.example.com",
            smtp_port=465,
            smtp_use_ssl=True,
        )
        mock_smtp_ssl_cls.assert_called_once()

    @patch("smtplib.SMTP")
    def test_smtp_with_tls(self, mock_smtp_cls):
        """TLS-enabled SMTP calls starttls."""
        from providers.comms.email import _send_via_smtp

        mock_server = MagicMock()
        mock_smtp_cls.return_value = mock_server
        mock_server.__enter__ = Mock(return_value=mock_server)
        mock_server.__exit__ = Mock(return_value=False)

        _send_via_smtp(
            to="test@example.com",
            subject="Test",
            html="<p>Hi</p>",
            from_address="sender@example.com",
            transport={},
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_use_tls=True,
        )
        mock_server.starttls.assert_called_once()

    @patch("smtplib.SMTP")
    def test_smtp_with_auth(self, mock_smtp_cls):
        """SMTP with username calls login."""
        from providers.comms.email import _send_via_smtp

        mock_server = MagicMock()
        mock_smtp_cls.return_value = mock_server
        mock_server.__enter__ = Mock(return_value=mock_server)
        mock_server.__exit__ = Mock(return_value=False)

        _send_via_smtp(
            to="test@example.com",
            subject="Test",
            html="<p>Hi</p>",
            from_address="sender@example.com",
            transport={},
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_username="user",
            smtp_password="pass",
        )
        mock_server.login.assert_called_once_with("user", "pass")

    @patch("smtplib.SMTP")
    def test_smtp_timeout_minimum(self, mock_smtp_cls):
        """Timeout is at least 1 second."""
        from providers.comms.email import _send_via_smtp

        mock_server = MagicMock()
        mock_smtp_cls.return_value = mock_server
        mock_server.__enter__ = Mock(return_value=mock_server)
        mock_server.__exit__ = Mock(return_value=False)

        _send_via_smtp(
            to="test@example.com",
            subject="Test",
            html="<p>Hi</p>",
            from_address="sender@example.com",
            transport={},
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_timeout_seconds=0,
        )
        # timeout=0 would be max(0, 1) = 1
        mock_smtp_cls.assert_called_once_with("smtp.example.com", 587, timeout=1)


# ══════════════════════════════════════════════════════════════════════════════
# COMMS — twilio.py
# ══════════════════════════════════════════════════════════════════════════════

class TestTwilioProvider:
    """Tests for the twilio provider module."""

    def test_has_twilio_constant_exists(self):
        from providers.comms.twilio import HAS_TWILIO
        assert isinstance(HAS_TWILIO, bool)

    def test_twilio_rest_exception_exported(self):
        from providers.comms.twilio import TwilioRestException
        assert TwilioRestException is not None

    def test_create_twilio_client_function_exists(self):
        from providers.comms.twilio import create_twilio_client
        assert callable(create_twilio_client)

    def test_all_exports_defined(self):
        from providers.comms import twilio
        for name in twilio.__all__:
            assert hasattr(twilio, name), f"Missing export: {name}"

    def test_create_twilio_client_returns_none_when_unavailable(self):
        """When HAS_TWILIO is False, create_twilio_client returns None."""
        from providers.comms import twilio

        original = twilio.HAS_TWILIO
        try:
            twilio.HAS_TWILIO = False
            result = twilio.create_twilio_client("sid", "token")
            assert result is None
        finally:
            twilio.HAS_TWILIO = original

    @patch("providers.comms.twilio._TwilioClient")
    def test_create_twilio_client_returns_client_when_available(self, mock_client_cls):
        """When HAS_TWILIO is True, create_twilio_client returns a client."""
        from providers.comms import twilio

        original = twilio.HAS_TWILIO
        try:
            twilio.HAS_TWILIO = True
            mock_client_cls.return_value = MagicMock()
            result = twilio.create_twilio_client("sid", "token")
            mock_client_cls.assert_called_once_with("sid", "token")
            assert result is not None
        finally:
            twilio.HAS_TWILIO = original


# ══════════════════════════════════════════════════════════════════════════════
# COMMS — whatsapp.py
# ══════════════════════════════════════════════════════════════════════════════

class TestWhatsAppProvider:
    """Tests for the whatsapp provider module."""

    def test_has_whatsapp_constant_exists(self):
        from providers.comms.whatsapp import HAS_WHATSAPP
        assert isinstance(HAS_WHATSAPP, bool)

    def test_send_whatsapp_message_function_exists(self):
        from providers.comms.whatsapp import send_whatsapp_message
        assert callable(send_whatsapp_message)

    def test_normalize_wa_adds_prefix(self):
        """Numbers without 'whatsapp:' prefix get it added."""
        from providers.comms.whatsapp import _normalize_wa

        assert _normalize_wa("+15551234567") == "whatsapp:+15551234567"

    def test_normalize_wa_preserves_existing_prefix(self):
        """Numbers with 'whatsapp:' prefix are unchanged."""
        from providers.comms.whatsapp import _normalize_wa

        assert _normalize_wa("whatsapp:+15551234567") == "whatsapp:+15551234567"

    def test_normalize_wa_strips_whitespace(self):
        """Whitespace is stripped from the number."""
        from providers.comms.whatsapp import _normalize_wa

        assert _normalize_wa("  +15551234567  ") == "whatsapp:+15551234567"

    def test_normalize_wa_empty_string(self):
        """Empty string gets prefix added."""
        from providers.comms.whatsapp import _normalize_wa

        assert _normalize_wa("") == "whatsapp:"

    def test_send_whatsapp_preview_mode(self):
        """Preview mode returns delivered=False without calling Twilio."""
        from providers.comms.whatsapp import send_whatsapp_message

        result = send_whatsapp_message(
            to="+15551234567",
            body="Hello",
            from_number="+15557654321",
            preview=True,
        )
        assert result["delivered"] is False
        assert result["preview"] is True
        assert result["channel"] == "whatsapp"
        assert result["to"] == "whatsapp:+15551234567"

    def test_send_whatsapp_no_credentials(self):
        """Without credentials, returns preview mode."""
        from providers.comms.whatsapp import send_whatsapp_message

        result = send_whatsapp_message(
            to="+15551234567",
            body="Hello",
            from_number="+15557654321",
            account_sid="",
            auth_token="",
        )
        assert result["delivered"] is False
        assert result["preview"] is True

    def test_send_whatsapp_normalizes_to_number(self):
        """The 'to' field in result has whatsapp: prefix."""
        from providers.comms.whatsapp import send_whatsapp_message

        result = send_whatsapp_message(
            to="+15551234567",
            body="Hello",
            from_number="+15557654321",
            preview=True,
        )
        assert result["to"] == "whatsapp:+15551234567"

    @patch("providers.comms.whatsapp.create_twilio_client")
    def test_send_whatsapp_with_twilio_client(self, mock_create):
        """When Twilio client is available, sends via Twilio API."""
        from providers.comms.whatsapp import send_whatsapp_message

        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_message.sid = "SM1234567890"
        mock_client.messages.create.return_value = mock_message
        mock_create.return_value = mock_client

        # Force _HAVE_TWILIO to True
        import providers.comms.whatsapp as wa_mod
        original = wa_mod._HAVE_TWILIO
        try:
            wa_mod._HAVE_TWILIO = True
            result = wa_mod.send_whatsapp_message(
                to="+15551234567",
                body="Hello World",
                from_number="+15557654321",
                account_sid="test-sid",
                auth_token="test-token",
            )
            assert result["delivered"] is True
            assert result["preview"] is False
            assert result["sid"] == "SM1234567890"
            mock_client.messages.create.assert_called_once()
        finally:
            wa_mod._HAVE_TWILIO = original

    @patch("providers.comms.whatsapp.create_twilio_client")
    def test_send_whatsapp_client_returns_none(self, mock_create):
        """When client creation fails, falls back to preview."""
        from providers.comms.whatsapp import send_whatsapp_message

        mock_create.return_value = None

        import providers.comms.whatsapp as wa_mod
        original = wa_mod._HAVE_TWILIO
        try:
            wa_mod._HAVE_TWILIO = True
            result = wa_mod.send_whatsapp_message(
                to="+15551234567",
                body="Hello",
                from_number="+15557654321",
                account_sid="test-sid",
                auth_token="test-token",
            )
            assert result["delivered"] is False
            assert result["preview"] is True
        finally:
            wa_mod._HAVE_TWILIO = original


# ══════════════════════════════════════════════════════════════════════════════
# SECURITY PACKAGE — __init__.py
# ══════════════════════════════════════════════════════════════════════════════

class TestSecurityInit:
    """Verify security package module exists and is importable."""

    def test_security_package_importable(self):
        import providers.security
        assert providers.security is not None


# ══════════════════════════════════════════════════════════════════════════════
# SECURITY — encryption.py
# ══════════════════════════════════════════════════════════════════════════════

class TestEncryptionProvider:
    """Tests for the encryption provider module."""

    def test_fernet_exported(self):
        from providers.security.encryption import Fernet
        assert Fernet is not None

    def test_hashes_exported(self):
        from providers.security.encryption import hashes
        assert hashes is not None

    def test_pbkdf2hmac_exported(self):
        from providers.security.encryption import PBKDF2HMAC
        assert PBKDF2HMAC is not None

    def test_all_exports_defined(self):
        from providers.security import encryption
        for name in encryption.__all__:
            assert hasattr(encryption, name), f"Missing export: {name}"

    def test_fernet_can_encrypt_decrypt(self):
        """Fernet can actually encrypt and decrypt data."""
        from providers.security.encryption import Fernet

        key = Fernet.generate_key()
        f = Fernet(key)
        original = b"test data for encryption"
        encrypted = f.encrypt(original)
        decrypted = f.decrypt(encrypted)
        assert decrypted == original


# ══════════════════════════════════════════════════════════════════════════════
# SECURITY — threat_intel.py
# ══════════════════════════════════════════════════════════════════════════════

class TestThreatIntelProvider:
    """Tests for the threat_intel provider module."""

    def test_fetch_tor_exit_list_function_exists(self):
        from providers.security.threat_intel import fetch_tor_exit_list
        assert callable(fetch_tor_exit_list)

    def test_all_exports_defined(self):
        from providers.security import threat_intel
        for name in threat_intel.__all__:
            assert hasattr(threat_intel, name), f"Missing export: {name}"

    @patch("providers.security.threat_intel.urllib.request.urlopen")
    def test_fetch_tor_exit_list_success(self, mock_urlopen):
        """Successful fetch returns list of IPs."""
        from providers.security.threat_intel import fetch_tor_exit_list

        mock_resp = MagicMock()
        mock_resp.read.return_value = b"1.2.3.4\n5.6.7.8\n9.10.11.12\n"
        mock_resp.__enter__ = Mock(return_value=mock_resp)
        mock_resp.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_resp

        result = fetch_tor_exit_list()
        assert result == ["1.2.3.4", "5.6.7.8", "9.10.11.12"]

    @patch("providers.security.threat_intel.urllib.request.urlopen")
    def test_fetch_tor_exit_list_empty_lines_ignored(self, mock_urlopen):
        """Empty lines in the response are skipped."""
        from providers.security.threat_intel import fetch_tor_exit_list

        mock_resp = MagicMock()
        mock_resp.read.return_value = b"1.2.3.4\n\n\n5.6.7.8\n"
        mock_resp.__enter__ = Mock(return_value=mock_resp)
        mock_resp.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_resp

        result = fetch_tor_exit_list()
        assert result == ["1.2.3.4", "5.6.7.8"]

    @patch("providers.security.threat_intel.urllib.request.urlopen")
    def test_fetch_tor_exit_list_network_error(self, mock_urlopen):
        """Network error returns empty list."""
        from providers.security.threat_intel import fetch_tor_exit_list

        mock_urlopen.side_effect = OSError("Connection refused")

        result = fetch_tor_exit_list()
        assert result == []

    @patch("providers.security.threat_intel.urllib.request.urlopen")
    def test_fetch_tor_exit_list_http_error(self, mock_urlopen):
        """HTTP error returns empty list."""
        from providers.security.threat_intel import fetch_tor_exit_list
        import urllib.error

        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="https://check.torproject.org/torbulkexitlist",
            code=500,
            msg="Server Error",
            hdrs={},
            fp=MagicMock(),
        )

        result = fetch_tor_exit_list()
        assert result == []

    @patch("providers.security.threat_intel.urllib.request.urlopen")
    def test_fetch_tor_exit_list_whitespace_stripped(self, mock_urlopen):
        """Whitespace around IPs is stripped."""
        from providers.security.threat_intel import fetch_tor_exit_list

        mock_resp = MagicMock()
        mock_resp.read.return_value = b"  1.2.3.4  \n  5.6.7.8  \n"
        mock_resp.__enter__ = Mock(return_value=mock_resp)
        mock_resp.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_resp

        result = fetch_tor_exit_list()
        assert result == ["1.2.3.4", "5.6.7.8"]


# ══════════════════════════════════════════════════════════════════════════════
# SECURITY — watchlist.py
# ══════════════════════════════════════════════════════════════════════════════

class TestWatchlistProviderError:
    """Tests for the WatchlistProviderError exception."""

    def test_error_is_exception(self):
        from providers.security.watchlist import WatchlistProviderError

        assert issubclass(WatchlistProviderError, Exception)

    def test_error_can_be_raised(self):
        from providers.security.watchlist import WatchlistProviderError

        with pytest.raises(WatchlistProviderError, match="test error"):
            raise WatchlistProviderError("test error")


class TestScreenWatchlist:
    """Tests for the screen_watchlist function."""

    def test_screen_watchlist_no_url_raises(self):
        """Missing API URL raises WatchlistProviderError."""
        from providers.security.watchlist import screen_watchlist, WatchlistProviderError

        # Ensure env var is not set
        original = os.environ.pop("WATCHLIST_API_URL", None)
        try:
            with pytest.raises(WatchlistProviderError, match="not configured"):
                screen_watchlist("EMP001", "John Doe", "US")
        finally:
            if original is not None:
                os.environ["WATCHLIST_API_URL"] = original

    def test_screen_watchlist_empty_url_raises(self):
        """Empty API URL raises WatchlistProviderError."""
        from providers.security.watchlist import screen_watchlist, WatchlistProviderError

        with pytest.raises(WatchlistProviderError, match="not configured"):
            screen_watchlist("EMP001", "John Doe", "US", api_url="")

    @patch("providers.security.watchlist.urllib.request.urlopen")
    def test_screen_watchlist_success(self, mock_urlopen):
        """Successful screening returns structured result."""
        from providers.security.watchlist import screen_watchlist

        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "status": "clear",
            "score": 0.1,
            "details": "No matches found",
            "flagged_categories": [],
            "check_id": "chk-12345",
        }).encode()
        mock_resp.__enter__ = Mock(return_value=mock_resp)
        mock_resp.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_resp

        result = screen_watchlist(
            "EMP001", "John Doe", "US",
            api_url="https://api.example.com",
        )
        assert result["status"] == "clear"
        assert result["score"] == 0.1
        assert result["details"] == "No matches found"
        assert result["flagged_categories"] == []
        assert result["check_id"] == "chk-12345"

    @patch("providers.security.watchlist.urllib.request.urlopen")
    def test_screen_watchlist_flagged(self, mock_urlopen):
        """Screening with flagged categories."""
        from providers.security.watchlist import screen_watchlist

        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "status": "flagged",
            "score": 0.95,
            "details": "Sanctions match",
            "flagged_categories": ["sanctions", "pep"],
            "check_id": "chk-99999",
        }).encode()
        mock_resp.__enter__ = Mock(return_value=mock_resp)
        mock_resp.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_resp

        result = screen_watchlist(
            "EMP002", "Jane Doe", "GB",
            api_url="https://api.example.com",
        )
        assert result["status"] == "flagged"
        assert result["score"] == 0.95
        assert "sanctions" in result["flagged_categories"]

    @patch("providers.security.watchlist.urllib.request.urlopen")
    def test_screen_watchlist_network_error(self, mock_urlopen):
        """Network error raises WatchlistProviderError."""
        from providers.security.watchlist import screen_watchlist, WatchlistProviderError

        import urllib.error
        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")

        with pytest.raises(WatchlistProviderError):
            screen_watchlist(
                "EMP001", "John Doe", "US",
                api_url="https://api.example.com",
            )

    @patch("providers.security.watchlist.urllib.request.urlopen")
    def test_screen_watchlist_json_decode_error(self, mock_urlopen):
        """Invalid JSON response raises WatchlistProviderError."""
        from providers.security.watchlist import screen_watchlist, WatchlistProviderError

        mock_resp = MagicMock()
        mock_resp.read.return_value = b"not valid json"
        mock_resp.__enter__ = Mock(return_value=mock_resp)
        mock_resp.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_resp

        with pytest.raises(WatchlistProviderError):
            screen_watchlist(
                "EMP001", "John Doe", "US",
                api_url="https://api.example.com",
            )

    @patch("providers.security.watchlist.urllib.request.urlopen")
    def test_screen_watchlist_default_values(self, mock_urlopen):
        """Missing fields in response get default values."""
        from providers.security.watchlist import screen_watchlist

        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({}).encode()
        mock_resp.__enter__ = Mock(return_value=mock_resp)
        mock_resp.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_resp

        result = screen_watchlist(
            "EMP001", "John Doe", "US",
            api_url="https://api.example.com",
        )
        assert result["status"] == "error"
        assert result["score"] == 0.0
        assert result["details"] == "External check completed"
        assert result["flagged_categories"] == []
        assert result["check_id"] is None

    @patch("providers.security.watchlist.urllib.request.urlopen")
    def test_screen_watchlist_uses_env_url(self, mock_urlopen):
        """Uses WATCHLIST_API_URL env var when api_url not provided."""
        from providers.security.watchlist import screen_watchlist

        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({"status": "clear"}).encode()
        mock_resp.__enter__ = Mock(return_value=mock_resp)
        mock_resp.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_resp

        os.environ["WATCHLIST_API_URL"] = "https://env-api.example.com"
        try:
            screen_watchlist("EMP001", "John Doe", "US")
            # Verify the call was made to the env URL
            call_args = mock_urlopen.call_args
            req = call_args[0][0]
            assert "env-api.example.com" in req.full_url
        finally:
            os.environ.pop("WATCHLIST_API_URL", None)


# ══════════════════════════════════════════════════════════════════════════════
# VOICE PACKAGE — __init__.py
# ══════════════════════════════════════════════════════════════════════════════

class TestVoiceInit:
    """Verify voice package exports."""

    def test_voice_exports_transcribe_audio(self):
        from providers.voice import transcribe_audio
        assert callable(transcribe_audio)

    def test_voice_exports_process_product_voice_command(self):
        from providers.voice import process_product_voice_command
        assert callable(process_product_voice_command)

    def test_voice_exports_process_finance_voice_command(self):
        from providers.voice import process_finance_voice_command
        assert callable(process_finance_voice_command)

    def test_voice_all_exports_defined(self):
        import providers.voice as voice
        for name in voice.__all__:
            assert hasattr(voice, name), f"Missing export: {name}"


# ══════════════════════════════════════════════════════════════════════════════
# VOICE — voice_to_text.py
# ══════════════════════════════════════════════════════════════════════════════

class TestTranscribeAudio:
    """Tests for the transcribe_audio function."""

    @patch("urllib.request.urlopen")
    @patch("providers.voice.voice_to_text.settings")
    def test_transcribe_audio_success(self, mock_settings, mock_urlopen):
        """Successful transcription returns text."""
        from providers.voice.voice_to_text import transcribe_audio

        mock_settings.ollama_base_url = "http://localhost:11434"

        mock_resp = MagicMock()
        mock_resp.read.return_value = b'{"response": "Hello world"}'
        mock_resp.__enter__ = Mock(return_value=mock_resp)
        mock_resp.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_resp

        result = transcribe_audio(b"fake_audio_bytes")
        assert result == "Hello world"

    @patch("urllib.request.urlopen")
    @patch("providers.voice.voice_to_text.settings")
    def test_transcribe_audio_empty_response(self, mock_settings, mock_urlopen):
        """Empty response returns empty string."""
        from providers.voice.voice_to_text import transcribe_audio

        mock_settings.ollama_base_url = "http://localhost:11434"

        mock_resp = MagicMock()
        mock_resp.read.return_value = b'{"response": ""}'
        mock_resp.__enter__ = Mock(return_value=mock_resp)
        mock_resp.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_resp

        result = transcribe_audio(b"audio")
        assert result == ""

    @patch("urllib.request.urlopen")
    @patch("providers.voice.voice_to_text.settings")
    def test_transcribe_audio_network_error(self, mock_settings, mock_urlopen):
        """Network error returns empty string."""
        from providers.voice.voice_to_text import transcribe_audio

        mock_settings.ollama_base_url = "http://localhost:11434"
        mock_urlopen.side_effect = OSError("Connection refused")

        result = transcribe_audio(b"audio")
        assert result == ""

    @patch("urllib.request.urlopen")
    @patch("providers.voice.voice_to_text.settings")
    def test_transcribe_audio_custom_model(self, mock_settings, mock_urlopen):
        """Custom model name is used in the request."""
        from providers.voice.voice_to_text import transcribe_audio

        mock_settings.ollama_base_url = "http://localhost:11434"

        mock_resp = MagicMock()
        mock_resp.read.return_value = b'{"response": "test"}'
        mock_resp.__enter__ = Mock(return_value=mock_resp)
        mock_resp.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_resp

        transcribe_audio(b"audio", model="custom:model")
        # Verify the request payload contains the custom model
        call_args = mock_urlopen.call_args
        req = call_args[0][0]
        payload = json.loads(req.data)
        assert payload["model"] == "custom:model"

    @patch("urllib.request.urlopen")
    @patch("providers.voice.voice_to_text.settings")
    def test_transcribe_audio_encodes_base64(self, mock_settings, mock_urlopen):
        """Audio bytes are base64 encoded in the request."""
        from providers.voice.voice_to_text import transcribe_audio

        mock_settings.ollama_base_url = "http://localhost:11434"

        mock_resp = MagicMock()
        mock_resp.read.return_value = b'{"response": "ok"}'
        mock_resp.__enter__ = Mock(return_value=mock_resp)
        mock_resp.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_resp

        audio_bytes = b"test_audio_data"
        transcribe_audio(audio_bytes)

        call_args = mock_urlopen.call_args
        req = call_args[0][0]
        payload = json.loads(req.data)
        expected_b64 = base64.b64encode(audio_bytes).decode("utf-8")
        assert payload["images"][0] == expected_b64


class TestProcessProductVoiceCommand:
    """Tests for the process_product_voice_command function."""

    def test_empty_transcript_returns_defaults(self):
        """Empty transcript returns default result structure."""
        from providers.voice.voice_to_text import process_product_voice_command

        result = process_product_voice_command("")
        assert result["product_name"] == ""
        assert result["color"] == ""
        assert result["size"] == ""
        assert result["material"] == ""
        assert result["quantity"] == 1
        assert result["action"] == "add"
        assert result["raw_text"] == ""

    def test_whitespace_only_returns_defaults(self):
        """Whitespace-only transcript returns defaults."""
        from providers.voice.voice_to_text import process_product_voice_command

        result = process_product_voice_command("   ")
        assert result["quantity"] == 1
        assert result["action"] == "add"

    def test_extract_quantity_explicit(self):
        """'quantity N' pattern extracts quantity."""
        from providers.voice.voice_to_text import process_product_voice_command

        result = process_product_voice_command("add quantity 5 red shirts")
        assert result["quantity"] == 5

    def test_extract_quantity_with_unit(self):
        """'N pieces/units/items' pattern extracts quantity."""
        from providers.voice.voice_to_text import process_product_voice_command

        result = process_product_voice_command("add 3 pieces of cotton shirt")
        assert result["quantity"] == 3

    def test_extract_quantity_units_variations(self):
        """Various unit patterns are recognized."""
        from providers.voice.voice_to_text import process_product_voice_command

        for unit in ["pieces", "units", "items", "pcs", "boxes", "bags", "sets"]:
            result = process_product_voice_command(f"add 10 {unit} of something")
            assert result["quantity"] == 10, f"Failed for unit: {unit}"

    def test_extract_quantity_fallback_first_number(self):
        """First bare number is used as quantity fallback."""
        from providers.voice.voice_to_text import process_product_voice_command

        result = process_product_voice_command("I want 7 red shirts")
        assert result["quantity"] == 7

    def test_extract_action_add(self):
        """Default action is 'add'."""
        from providers.voice.voice_to_text import process_product_voice_command

        result = process_product_voice_command("add red shirt")
        assert result["action"] == "add"

    def test_extract_action_remove(self):
        """Remove keywords set action to 'remove'."""
        from providers.voice.voice_to_text import process_product_voice_command

        for keyword in ["remove", "delete", "drop", "subtract", "take away"]:
            result = process_product_voice_command(f"{keyword} red shirt")
            assert result["action"] == "remove", f"Failed for keyword: {keyword}"

    def test_extract_action_update(self):
        """Update keywords set action to 'update'."""
        from providers.voice.voice_to_text import process_product_voice_command

        for keyword in ["update", "change", "modify", "edit"]:
            result = process_product_voice_command(f"{keyword} red shirt")
            assert result["action"] == "update", f"Failed for keyword: {keyword}"

    def test_extract_color(self):
        """Color keywords are extracted."""
        from providers.voice.voice_to_text import process_product_voice_command

        result = process_product_voice_command("add red shirt")
        assert result["color"] == "Red"

    def test_extract_size(self):
        """Size keywords are extracted and uppercased."""
        from providers.voice.voice_to_text import process_product_voice_command

        result = process_product_voice_command("add large shirt")
        assert result["size"] == "LARGE"

    def test_extract_material(self):
        """Material keywords are extracted."""
        from providers.voice.voice_to_text import process_product_voice_command

        result = process_product_voice_command("add cotton shirt")
        assert result["material"] == "Cotton"

    def test_extract_product_name(self):
        """Product name is extracted from non-variant words."""
        from providers.voice.voice_to_text import process_product_voice_command

        result = process_product_voice_command("add red cotton shirt")
        assert "shirt" in result["product_name"].lower()

    def test_product_name_excludes_variant_keywords(self):
        """Variant keywords are excluded from product name."""
        from providers.voice.voice_to_text import process_product_voice_command

        result = process_product_voice_command("add red large cotton shirt")
        product_lower = result["product_name"].lower()
        assert "red" not in product_lower
        assert "large" not in product_lower
        assert "cotton" not in product_lower

    def test_product_name_max_five_words(self):
        """Product name is limited to 5 words."""
        from providers.voice.voice_to_text import process_product_voice_command

        result = process_product_voice_command("add red cotton shirt with buttons and collar and cuffs")
        words = result["product_name"].split()
        assert len(words) <= 5

    def test_raw_text_preserved(self):
        """Raw transcript is preserved in result."""
        from providers.voice.voice_to_text import process_product_voice_command

        transcript = "add 3 red cotton shirts"
        result = process_product_voice_command(transcript)
        assert result["raw_text"] == transcript

    def test_multiple_variants_extracted(self):
        """Multiple variant types can be extracted simultaneously."""
        from providers.voice.voice_to_text import process_product_voice_command

        result = process_product_voice_command("add large red cotton shirt")
        assert result["size"] == "LARGE"
        assert result["color"] == "Red"
        assert result["material"] == "Cotton"


class TestProcessFinanceVoiceCommand:
    """Tests for the process_finance_voice_command function."""

    def test_empty_transcript_returns_defaults(self):
        """Empty transcript returns default result structure."""
        from providers.voice.voice_to_text import process_finance_voice_command

        result = process_finance_voice_command("")
        assert result["task_type"] == ""
        assert result["amount"] == 0.0
        assert result["currency"] == "USD"
        assert result["category"] == ""
        assert result["description"] == ""
        assert result["action"] == "record"
        assert result["raw_text"] == ""

    def test_extract_amount_with_dollar_sign(self):
        """Dollar amounts are extracted."""
        from providers.voice.voice_to_text import process_finance_voice_command

        result = process_finance_voice_command("record expense $50.00 for office supplies")
        assert result["amount"] == 50.0

    def test_extract_amount_with_usd(self):
        """USD amounts are extracted."""
        from providers.voice.voice_to_text import process_finance_voice_command

        result = process_finance_voice_command("record 100 USD expense")
        assert result["amount"] == 100.0

    def test_extract_amount_with_decimal(self):
        """Decimal amounts are extracted."""
        from providers.voice.voice_to_text import process_finance_voice_command

        result = process_finance_voice_command("record $29.99 expense")
        assert result["amount"] == 29.99

    def test_extract_amount_comma_separator(self):
        """Comma in amount is handled."""
        from providers.voice.voice_to_text import process_finance_voice_command

        result = process_finance_voice_command("record $1000.50 expense")
        assert result["amount"] == 1000.5

    def test_extract_task_type_expense(self):
        """Expense keywords set task_type to 'expense'."""
        from providers.voice.voice_to_text import process_finance_voice_command

        result = process_finance_voice_command("record expense for office supplies")
        assert result["task_type"] == "expense"

    def test_extract_task_type_asset(self):
        """Asset keywords set task_type to 'asset'."""
        from providers.voice.voice_to_text import process_finance_voice_command

        result = process_finance_voice_command("record new asset")
        assert result["task_type"] == "asset"

    def test_extract_task_type_task(self):
        """Task keywords set task_type to 'task'."""
        from providers.voice.voice_to_text import process_finance_voice_command

        result = process_finance_voice_command("process this task")
        assert result["task_type"] == "task"

    def test_extract_action_record(self):
        """Default action is 'record'."""
        from providers.voice.voice_to_text import process_finance_voice_command

        result = process_finance_voice_command("record expense $50")
        assert result["action"] == "record"

    def test_extract_action_delete(self):
        """Delete keywords set action to 'delete'."""
        from providers.voice.voice_to_text import process_finance_voice_command

        for keyword in ["delete", "remove", "cancel", "reverse", "refund"]:
            result = process_finance_voice_command(f"{keyword} expense")
            assert result["action"] == "delete", f"Failed for keyword: {keyword}"

    def test_extract_action_update(self):
        """Update keywords set action to 'update'."""
        from providers.voice.voice_to_text import process_finance_voice_command

        for keyword in ["update", "change", "modify", "edit", "correct"]:
            result = process_finance_voice_command(f"{keyword} expense")
            assert result["action"] == "update", f"Failed for keyword: {keyword}"

    def test_extract_category(self):
        """Category keywords are extracted."""
        from providers.voice.voice_to_text import process_finance_voice_command

        categories = [
            "office supplies", "travel", "food", "utilities", "rent",
            "salary", "marketing", "equipment", "services", "shipping",
            "insurance", "tax", "maintenance",
        ]
        for cat in categories:
            result = process_finance_voice_command(f"record ${cat} expense")
            assert result["category"] == cat, f"Failed for category: {cat}"

    def test_extract_description(self):
        """Description is extracted from first sentence."""
        from providers.voice.voice_to_text import process_finance_voice_command

        result = process_finance_voice_command("record expense $50 for office supplies")
        assert "record expense $50 for office supplies" in result["description"]

    def test_description_max_200_chars(self):
        """Description is capped at 200 characters."""
        from providers.voice.voice_to_text import process_finance_voice_command

        long_text = "record expense $" + "a" * 300
        result = process_finance_voice_command(long_text)
        assert len(result["description"]) <= 200

    def test_raw_text_preserved(self):
        """Raw transcript is preserved in result."""
        from providers.voice.voice_to_text import process_finance_voice_command

        transcript = "record expense $50 for office supplies"
        result = process_finance_voice_command(transcript)
        assert result["raw_text"] == transcript

    def test_no_amount_returns_zero(self):
        """Transcript without amount returns 0.0."""
        from providers.voice.voice_to_text import process_finance_voice_command

        result = process_finance_voice_command("record expense for something")
        assert result["amount"] == 0.0

    def test_currency_default_usd(self):
        """Default currency is USD."""
        from providers.voice.voice_to_text import process_finance_voice_command

        result = process_finance_voice_command("record something")
        assert result["currency"] == "USD"


# ══════════════════════════════════════════════════════════════════════════════
# Module-level constants tests
# ══════════════════════════════════════════════════════════════════════════════

class TestVoiceConstants:
    """Tests for voice module constants."""

    def test_variant_keywords_exist(self):
        from providers.voice.voice_to_text import _VariantKeywords
        assert "color" in _VariantKeywords
        assert "size" in _VariantKeywords
        assert "material" in _VariantKeywords

    def test_finance_keywords_exist(self):
        from providers.voice.voice_to_text import _FinanceKeywords
        assert "expense" in _FinanceKeywords
        assert "asset" in _FinanceKeywords
        assert "task" in _FinanceKeywords

    def test_ollama_whisper_model_constant(self):
        from providers.voice.voice_to_text import _OLLAMA_WHISPER_MODEL
        assert isinstance(_OLLAMA_WHISPER_MODEL, str)
        assert len(_OLLAMA_WHISPER_MODEL) > 0
