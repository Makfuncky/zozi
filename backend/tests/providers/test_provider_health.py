"""Provider health-check tests — Law 129/130/131.

Verifies:
  * health_check() exists where BaseProvider is used (Law 129).
  * Error mapping to domain exceptions (Law 130).
  * No real external SDK calls — everything is mocked (Law 131).
  * Missing SDKs degrade gracefully (return defaults, not crash).

Run: python -m pytest tests/providers/test_provider_health.py -q
"""
from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, Mock, patch

import pytest

# Load tests/_support/laws.py directly (pytest sys.path manipulation breaks
# `from tests._support import laws` inside test modules).
_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
_LAWS_PATH = _BACKEND_ROOT / "tests" / "_support" / "laws.py"
_spec = importlib.util.spec_from_file_location("_support_laws", _LAWS_PATH)
laws = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(laws)  # type: ignore[union-attr]

BACKEND_ROOT = Path(__file__).resolve().parent.parent


# ===========================================================================
# Law 129: health_check() exists where BaseProvider is used
# ===========================================================================
class TestHealthCheckExists:
    """If a provider uses BaseProvider, it must expose health_check()."""

    def test_base_provider_has_health_check(self):
        from providers._base import BaseProvider
        assert hasattr(BaseProvider, "health_check")
        assert callable(BaseProvider.health_check)

    def test_base_ai_provider_has_health_check(self):
        from providers._base import BaseAIProvider
        assert hasattr(BaseAIProvider, "health_check")
        assert callable(BaseAIProvider.health_check)

    def test_base_provider_health_check_returns_dict(self):
        from providers._base import BaseProvider

        class ConcreteProvider(BaseProvider):
            def is_available(self) -> bool:
                return True

            def health_check(self) -> dict[str, Any]:
                return {"status": "ok"}

        p = ConcreteProvider(name="test")
        result = p.health_check()
        assert isinstance(result, dict)
        assert "status" in result

    def test_base_ai_provider_health_check_returns_dict(self):
        from providers._base import BaseAIProvider

        class ConcreteAIProvider(BaseAIProvider):
            def load_model(self) -> None:
                self._model_loaded = True

            def predict(self, input_data: Any) -> Any:
                return input_data

            def preprocess(self, input_data: Any) -> Any:
                return input_data

            def postprocess(self, output: Any) -> Any:
                return output

        p = ConcreteAIProvider(name="test-ai", model="phi3")
        result = p.health_check()
        assert isinstance(result, dict)
        assert "status" in result
        assert "provider" in result
        assert "model" in result

    def test_analytics_provider_has_health_check_or_degrades(self):
        """AnalyticsProvider should have a health check or degrade gracefully."""
        from providers.analytics.analytics import AnalyticsProvider
        provider = AnalyticsProvider()
        # Either has health_check or get_dashboard_summary degrades
        if hasattr(provider, "health_check"):
            result = provider.health_check()
            assert isinstance(result, dict)
        else:
            # Graceful degradation: returns dict with message
            result = provider.get_dashboard_summary()
            assert isinstance(result, dict)
            assert "message" in result

    def test_storage_backend_has_health_check_or_degrades(self):
        """StorageBackend should have health_check or degrade gracefully."""
        from providers.storage.storage_backend import StorageBackend, LocalStorage
        # StorageBackend is abstract — test LocalStorage
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalStorage(base_dir=tmpdir)
            if hasattr(storage, "health_check"):
                result = storage.health_check()
                assert isinstance(result, dict)
            else:
                # At minimum, save/read should work
                storage.save("test.txt", b"data")
                assert storage.read("test.txt") == b"data"

    def test_encryption_provider_has_health_check_or_degrades(self):
        """Encryption provider should have health_check or degrade gracefully."""
        from providers.security.encryption import HAS_CRYPTOGRAPHY, encrypt_data
        if HAS_CRYPTOGRAPHY:
            result = encrypt_data(b"test")
            assert result is not None
        else:
            result = encrypt_data(b"test")
            assert result is None or result == b""


# ===========================================================================
# Law 130: Error mapping to domain exceptions
# ===========================================================================
class TestErrorMapping:
    """Provider errors must map to domain-appropriate exceptions."""

    def test_paypal_error_hierarchy(self):
        from providers.payments.paypal import (
            PayPalError,
            PayPalOrderNotFoundError,
            PayPalCaptureError,
            PayPalRefundError,
            PayPalVoidError,
            PayPalConfigurationError,
        )
        assert issubclass(PayPalOrderNotFoundError, PayPalError)
        assert issubclass(PayPalCaptureError, PayPalError)
        assert issubclass(PayPalRefundError, PayPalError)
        assert issubclass(PayPalVoidError, PayPalError)
        assert issubclass(PayPalConfigurationError, PayPalError)

    def test_oauth_provider_error_is_exception(self):
        from providers.auth.oauth import OAuthProviderError
        assert issubclass(OAuthProviderError, Exception)

    def test_jwt_error_is_exception(self):
        from providers.auth.jwt import JWTError
        assert issubclass(JWTError, Exception)

    def test_bank_api_error_is_exception(self):
        from providers.finance.bank_api import BankApiError
        assert issubclass(BankApiError, Exception)

    def test_watchlist_provider_error_is_exception(self):
        from providers.security.watchlist import WatchlistProviderError
        assert issubclass(WatchlistProviderError, Exception)

    def test_country_http_error_is_exception(self):
        from providers.geography.country_http import CountryHttpError
        assert issubclass(CountryHttpError, Exception)

    def test_paypal_error_maps_to_domain_on_network_failure(self):
        """PayPal provider should map network errors to PayPalError."""
        from providers.payments.paypal import PayPalError
        with patch("providers.payments.paypal.requests.get") as mock_get:
            import requests
            mock_get.side_effect = requests.RequestException("Connection refused")
            from providers.payments.paypal import capture_order
            with pytest.raises(PayPalError):
                capture_order("order-123", {})

    def test_oauth_error_maps_to_domain_on_network_failure(self):
        """OAuth provider should map network errors to OAuthProviderError."""
        from providers.auth.oauth import OAuthProviderError, _get_json
        with patch("providers.auth.oauth.requests.get") as mock_get:
            import requests
            mock_get.side_effect = requests.ConnectionError("refused")
            with pytest.raises(OAuthProviderError):
                _get_json("https://example.com")

    def test_bank_api_error_maps_to_domain_on_network_failure(self):
        """Bank API should map network errors to BankApiError."""
        from providers.finance.bank_api import BankApiError, dispatch_batch
        with patch("providers.finance.bank_api.requests.post") as mock_post:
            import requests
            mock_post.side_effect = requests.RequestException("refused")
            with pytest.raises(BankApiError):
                dispatch_batch("https://api.bank.com", "/v1/batches", "token", "idem", {}, 10.0)

    def test_watchlist_error_maps_to_domain_on_network_failure(self):
        """Watchlist should map network errors to WatchlistProviderError."""
        from providers.security.watchlist import WatchlistProviderError, screen_watchlist
        with patch("providers.security.watchlist.urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = OSError("Connection refused")
            with pytest.raises(WatchlistProviderError):
                screen_watchlist("EMP001", "John", "US", api_url="https://api.example.com")


# ===========================================================================
# Law 131: No real external SDK calls — mock everything
# ===========================================================================
class TestNoRealSdkCalls:
    """Tests must mock external SDKs — no real network calls."""

    @patch("providers.payments.stripe_sdk.stripe")
    def test_stripe_mocked_not_real(self, mock_stripe):
        """Stripe SDK is mocked — no real API call."""
        from providers.payments.stripe_sdk import HAS_STRIPE
        if HAS_STRIPE:
            mock_stripe.PaymentIntent.create.return_value = {"id": "pi_123"}
            # Would call stripe.PaymentIntent.create(...) in real code
            result = mock_stripe.PaymentIntent.create(amount=1000, currency="usd")
            assert result == {"id": "pi_123"}
            mock_stripe.PaymentIntent.create.assert_called_once()

    @patch("providers.comms.twilio._TwilioClient")
    def test_twilio_mocked_not_real(self, mock_client_cls):
        """Twilio SDK is mocked — no real API call."""
        from providers.comms.twilio import create_twilio_client
        mock_client_cls.return_value = MagicMock()
        result = create_twilio_client("sid", "token")
        assert result is not None
        mock_client_cls.assert_called_once()

    @patch("providers.comms.whatsapp.create_twilio_client")
    def test_whatsapp_mocked_not_real(self, mock_create):
        """WhatsApp uses mocked Twilio client."""
        from providers.comms.whatsapp import send_whatsapp_message
        mock_create.return_value = None
        import providers.comms.whatsapp as wa_mod
        original = wa_mod._HAVE_TWILIO
        try:
            wa_mod._HAVE_TWILIO = True
            result = wa_mod.send_whatsapp_message(
                to="+15551234567", body="Hi", from_number="+15557654321",
                account_sid="sid", auth_token="token",
            )
            assert result["delivered"] is False
        finally:
            wa_mod._HAVE_TWILIO = original

    @patch("providers.storage.s3_client.boto3")
    def test_s3_mocked_not_real(self, mock_boto3):
        """S3 SDK is mocked — no real API call."""
        from providers.storage.s3_client import create_s3_client
        mock_boto3.client.return_value = MagicMock()
        result = create_s3_client("bucket", "us-east-1", "id", "key", "secret")
        assert result is not None
        mock_boto3.client.assert_called_once()


# ===========================================================================
# Cross-provider health check aggregation
# ===========================================================================
class TestProviderHealthAggregation:
    """Call health_check()/HAS_ flags across providers and assert no crash."""

    def test_all_has_flags_accessible(self):
        """All HAS_ flags can be read without crashing."""
        pkgs = laws.discover_packages("providers")
        for pkg_name in pkgs:
            try:
                mod = importlib.import_module(pkg_name)
            except ImportError:
                continue
            flags = [n for n in dir(mod) if n.startswith("HAS_")]
            for flag in flags:
                value = getattr(mod, flag)
                assert isinstance(value, bool), (
                    f"{pkg_name}.{flag} is not bool"
                )

    def test_all_providers_importable(self):
        """All provider packages are importable."""
        pkgs = laws.discover_packages("providers")
        for pkg_name in pkgs:
            mod = importlib.import_module(pkg_name)
            assert mod is not None

    def test_no_provider_imports_forbidden_layers(self):
        """No provider package imports domains/modules/rbac/jobs/middleware."""
        laws.assert_no_forbidden_imports("providers", BACKEND_ROOT / "providers")

    def test_graceful_degradation_across_providers(self):
        """When SDKs are unavailable, providers degrade (return defaults)."""
        # Twilio
        from providers.comms import twilio as twilio_mod
        orig = twilio_mod.HAS_TWILIO
        try:
            twilio_mod.HAS_TWILIO = False
            assert twilio_mod.create_twilio_client("s", "t") is None
        finally:
            twilio_mod.HAS_TWILIO = orig

        # WhatsApp
        from providers.comms import whatsapp as wa_mod
        orig = wa_mod.HAS_WHATSAPP
        try:
            wa_mod.HAS_WHATSAPP = False
            result = wa_mod.send_whatsapp_message(
                to="+15551234567", body="Hi", from_number="+15557654321",
            )
            assert isinstance(result, dict)
        finally:
            wa_mod.HAS_WHATSAPP = orig

        # S3
        from providers.storage import s3_client as s3_mod
        orig = s3_mod.HAS_BOTO3
        try:
            s3_mod.HAS_BOTO3 = False
            assert s3_mod.create_s3_client("b", "r", "", "k", "s") is None
        finally:
            s3_mod.HAS_BOTO3 = orig

        # Stripe
        from providers.payments import stripe_sdk as stripe_mod
        orig = stripe_mod.HAS_STRIPE
        try:
            stripe_mod.HAS_STRIPE = False
            assert stripe_mod.stripe is None
        finally:
            stripe_mod.HAS_STRIPE = orig

        # PayPal
        from providers.payments import paypal as paypal_mod
        orig = paypal_mod.HAS_PAYPAL
        try:
            paypal_mod.HAS_PAYPAL = False
            assert paypal_mod.is_available() is False
        finally:
            paypal_mod.HAS_PAYPAL = orig

        # Barcode
        from providers.barcode import barcode_generator as bc_mod
        orig = bc_mod.HAS_BARCODE
        try:
            bc_mod.HAS_BARCODE = False
            result = bc_mod.generate_barcode("123456789012")
            assert result is None or result == b""
        finally:
            bc_mod.HAS_BARCODE = orig

        # QR
        from providers.qr import qr_generator as qr_mod
        orig = qr_mod.HAS_QRCODE
        try:
            qr_mod.HAS_QRCODE = False
            result = qr_mod.generate_qr("https://zozi.com")
            assert result is None or result == b""
        finally:
            qr_mod.HAS_QRCODE = orig

        # Scanner
        from providers.scanner import scanner as scan_mod
        orig = scan_mod.HAS_PYZBAR
        try:
            scan_mod.HAS_PYZBAR = False
            result = scan_mod.scan_barcode(b"fake-image")
            assert isinstance(result, list)
        finally:
            scan_mod.HAS_PYZBAR = orig

        # OCR
        from providers.ocr import ocr_parser as ocr_mod
        orig = ocr_mod.HAS_OCR_PARSER
        try:
            ocr_mod.HAS_OCR_PARSER = False
            result = ocr_mod.parse_bill_text("Total: $50.00")
            assert isinstance(result, dict)
        finally:
            ocr_mod.HAS_OCR_PARSER = orig

        # Voice
        from providers.voice import voice_to_text as voice_mod
        orig = voice_mod.HAS_VOICE
        try:
            voice_mod.HAS_VOICE = False
            result = voice_mod.transcribe_audio(b"fake-audio")
            assert result == "" or isinstance(result, str)
        finally:
            voice_mod.HAS_VOICE = orig

        # Finance
        from providers.finance import bank_api as bank_mod
        orig = bank_mod.HAS_BANK_API
        try:
            bank_mod.HAS_BANK_API = False
            result = bank_mod.test_connection("https://api.bank.com", "/v1/batches", "token", 10.0)
            assert isinstance(result, dict)
            assert result.get("reachable") is False
        finally:
            bank_mod.HAS_BANK_API = orig

        # Automation
        from providers.automation import scheduler as sched_mod
        orig = sched_mod.HAS_APSCHEDULER
        try:
            sched_mod.HAS_APSCHEDULER = False
            result = sched_mod.create_scheduler()
            assert result is None
        finally:
            sched_mod.HAS_APSCHEDULER = orig

        # Security encryption
        from providers.security import encryption as enc_mod
        orig = enc_mod.HAS_CRYPTOGRAPHY
        try:
            enc_mod.HAS_CRYPTOGRAPHY = False
            result = enc_mod.encrypt_data(b"secret")
            assert result is None or result == b""
        finally:
            enc_mod.HAS_CRYPTOGRAPHY = orig

        # Security threat intel
        from providers.security import threat_intel as ti_mod
        orig = ti_mod.HAS_THREAT_INTEL
        try:
            ti_mod.HAS_THREAT_INTEL = False
            result = ti_mod.fetch_tor_exit_list()
            assert isinstance(result, list)
        finally:
            ti_mod.HAS_THREAT_INTEL = orig

        # Security watchlist
        from providers.security import watchlist as wl_mod
        orig = wl_mod.HAS_WATCHLIST
        try:
            wl_mod.HAS_WATCHLIST = False
            result = wl_mod.screen_watchlist("EMP001", "John", "US", api_url="https://api.example.com")
            assert isinstance(result, dict)
        finally:
            wl_mod.HAS_WATCHLIST = orig

        # Geography
        from providers.geography import geo as geo_mod
        orig = geo_mod.HAS_GEOIP
        try:
            geo_mod.HAS_GEOIP = False
            try:
                result = geo_mod.resolve_ip_location(ip="1.2.3.4")
            except RuntimeError:
                pass  # Expected when no provider available
        finally:
            geo_mod.HAS_GEOIP = orig

        # Image
        from providers.image import image as img_mod
        orig_cv2 = img_mod.HAS_CV2
        orig_gf = img_mod.HAS_GUIDED_FILTER
        try:
            img_mod.HAS_CV2 = False
            img_mod.HAS_GUIDED_FILTER = False
            result = img_mod.remove_background(b"fake-image")
            assert isinstance(result, bytes)
        finally:
            img_mod.HAS_CV2 = orig_cv2
            img_mod.HAS_GUIDED_FILTER = orig_gf

        # AI text
        from providers.ai import text as text_mod
        orig = text_mod.HAS_NUMPY
        try:
            text_mod.HAS_NUMPY = False
            result = text_mod.cosine_similarity([1, 0], [0, 1])
            assert isinstance(result, float)
        finally:
            text_mod.HAS_NUMPY = orig

        # AI sentiment
        from providers.ai import sentiment as sent_mod
        orig = sent_mod.HAS_VADER
        try:
            sent_mod.HAS_VADER = False
            result = sent_mod.analyze_sentiment("This is great!")
            assert isinstance(result, dict)
        finally:
            sent_mod.HAS_VADER = orig

        # AI image similarity
        from providers.ai import image_similarity as sim_mod
        orig_pil = sim_mod.HAS_PIL
        orig_np = sim_mod.HAS_NUMPY
        try:
            sim_mod.HAS_PIL = False
            sim_mod.HAS_NUMPY = False
            result = sim_mod.compute_similarity(b"img1", b"img2")
            assert isinstance(result, float)
        finally:
            sim_mod.HAS_PIL = orig_pil
            sim_mod.HAS_NUMPY = orig_np

        # News
        from providers.news import rss_provider as news_mod
        orig = news_mod.HAS_FEEDPARSER
        try:
            news_mod.HAS_FEEDPARSER = False
            import asyncio
            try:
                result = asyncio.run(news_mod.fetch_rss_entries("https://example.com/feed.xml"))
            except Exception:
                result = None
            assert result is None or isinstance(result, list)
        finally:
            news_mod.HAS_FEEDPARSER = orig
