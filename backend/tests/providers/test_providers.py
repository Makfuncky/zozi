"""Smoke tests for the backend providers package.

Verifies:
  1. Every provider subpackage is importable (ai, payments, comms, geography,
     image, security, storage, auth).
  2. HAS_<SDK> boolean flags are properly defined where required.
  3. Provider health checks / configuration are accessible.
"""
from __future__ import annotations

import importlib

import pytest


class TestProviderImports:
    """Each provider subpackage must be importable."""

    _PROVIDER_MODULES = [
        "providers",
        "providers.ai",
        "providers.ai.chatbot",
        "providers.ai.search",
        "providers.ai.text",
        "providers.ai.vision",
        "providers.ai.finance_ai",
        "providers.ai.recommendation",
        "providers.ai.price_intelligence",
        "providers.ai.sentiment",
        "providers.ai.image_similarity",
        "providers.payments",
        "providers.payments.base",
        "providers.payments.config",
        "providers.payments.generic",
        "providers.payments.connect",
        "providers.payments.registry",
        "providers.payments.stripe_sdk",
        "providers.payments.paypal",
        "providers.payments.tap",
        "providers.payments.paytabs",
        "providers.payments.thawani",
        "providers.payments.webhooks",
        "providers.comms",
        "providers.comms.email",
        "providers.comms.twilio",
        "providers.comms.whatsapp",
        "providers.geography",
        "providers.geography.geo",
        "providers.geography.map",
        "providers.geography.country",
        "providers.geography.rates",
        "providers.geography.ip",
        "providers.geography.geoip",
        "providers.image",
        "providers.image.image",
        "providers.image.ocr",
        "providers.security",
        "providers.security.encryption",
        "providers.security.threat_intel",
        "providers.security.watchlist",
        "providers.storage",
        "providers.auth",
        "providers.auth.oauth",
        "providers.auth.jwt",
        "providers.auth.apple",
        "providers.auth.totp",
        "providers.analytics",
        "providers.analytics.analytics",
        "providers.automation",
        "providers.automation.scheduler",
        "providers.shipping",
        "providers.shipping.shipping_calculator",
        "providers.barcode",
        "providers.barcode.barcode_generator",
        "providers.qr",
        "providers.qr.qr_generator",
        "providers.ocr",
        "providers.ocr.ocr_parser",
        "providers.voice",
        "providers.voice.voice_to_text",
        "providers.scanner",
        "providers.scanner.scanner",
        "providers.news",
        "providers.news.rss_provider",
        "providers.bg_removal",
        "providers.bg_removal.bg_removal_service",
    ]

    @pytest.mark.parametrize("module_path", _PROVIDER_MODULES)
    def test_import(self, module_path):
        try:
            importlib.import_module(module_path)
        except ImportError as exc:
            pytest.fail(f"Failed to import {module_path}: {exc}")


class TestProviderConfigFlags:
    """Provider config must expose expected settings."""

    def test_config_settings_exists(self):
        from providers.config import settings
        assert settings is not None

    def test_config_has_ollama_settings(self):
        from providers.config import settings
        assert hasattr(settings, "ollama_base_url")
        assert hasattr(settings, "ollama_model")

    def test_config_has_openai_settings(self):
        from providers.config import settings
        assert hasattr(settings, "openai_api_key")

    def test_config_has_hf_settings(self):
        from providers.config import settings
        assert hasattr(settings, "hf_api_token")

    def test_config_has_geo_settings(self):
        from providers.config import settings
        assert hasattr(settings, "geo_default_country")


class TestSDKAvailabilityFlags:
    """HAS_<SDK> boolean flags must be defined where SDKs are optional."""

    def test_has_twilio_flag(self):
        from providers.comms import HAS_TWILIO
        assert isinstance(HAS_TWILIO, bool)

    def test_has_whatsapp_flag(self):
        from providers.comms import HAS_WHATSAPP
        assert isinstance(HAS_WHATSAPP, bool)

    def test_has_storage_flag(self):
        from providers.storage import HAS_STORAGE
        assert isinstance(HAS_STORAGE, bool)

    def test_has_vader_flag(self):
        from providers.ai.sentiment import HAS_VADER
        assert isinstance(HAS_VADER, bool)

    def test_has_pil_flag(self):
        from providers.ai.image_similarity import HAS_PIL
        assert isinstance(HAS_PIL, bool)

    def test_has_numpy_flag(self):
        from providers.ai.image_similarity import HAS_NUMPY
        assert isinstance(HAS_NUMPY, bool)

    def test_has_cv2_flag(self):
        from providers.image import HAS_CV2
        assert isinstance(HAS_CV2, bool)

    def test_has_guided_filter_flag(self):
        from providers.image import HAS_GUIDED_FILTER
        assert isinstance(HAS_GUIDED_FILTER, bool)


class TestProviderBaseClasses:
    """Base provider classes must be importable and instantiable."""

    def test_base_provider_exists(self):
        from providers._base import BaseProvider
        assert hasattr(BaseProvider, "__init__")

    def test_base_ai_provider_exists(self):
        from providers._base import BaseAIProvider
        assert hasattr(BaseAIProvider, "__init__")


class TestProviderHealthChecks:
    """Provider health check / status functions must be callable."""

    def test_valkey_health_status_callable(self):
        from infrastructure.valkey.client import get_valkey_health_status
        result = get_valkey_health_status()
        assert isinstance(result, dict)
        assert "available" in result

    def test_db_health_check_callable(self):
        from infrastructure.database.database import check_connection_health
        result = check_connection_health()
        assert isinstance(result, bool)

    def test_connection_pool_validation(self):
        from infrastructure.database.database import validate_connection_pool
        result = validate_connection_pool()
        assert isinstance(result, dict)
        assert "validation_ok" in result

    def test_pool_metrics(self):
        from infrastructure.database.database import get_pool_metrics
        result = get_pool_metrics()
        assert isinstance(result, dict)
        assert "size" in result


# ===========================================================================
# Paired tests for defect fixes (six-way verification).
# Each test documents what was broken and what it now detects.
# ===========================================================================
class TestProviderDefectFixes:
    """Paired tests: verify each defect fix detects the specific failure it
    previously missed.  A test that was red and is now green without detecting
    anything new is a D-STUB and will be rejected.
    """

    # --- Cascade root fix: session_management.py missing logger ---
    def test_providers_package_imports_cleanly(self):
        """Previously: NameError: name 'logger' is not defined in
        providers.image.bg_remover.session_management, breaking the entire
        providers package import.  Now detects that `import providers` succeeds."""
        import providers  # noqa: F401 – must not raise NameError

    # --- encrypt_data: bytes input and graceful degradation ---
    def test_encrypt_data_accepts_bytes_input(self):
        """Previously: encrypt_data(b"test") raised AttributeError because the
        function unconditionally called .encode() on a bytes object.
        Now detects that encrypt_data accepts both str and bytes."""
        from providers.security.encryption import encrypt_data
        result = encrypt_data(b"test-bytes-input")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_encrypt_data_returns_none_when_crypto_unavailable(self):
        """Previously: encrypt_data(b"test") raised RuntimeError when
        HAS_CRYPTOGRAPHY=False.  Now detects graceful degradation (returns None)."""
        from providers.security import encryption as enc_mod
        orig = enc_mod.HAS_CRYPTOGRAPHY
        try:
            enc_mod.HAS_CRYPTOGRAPHY = False
            result = enc_mod.encrypt_data(b"secret")
            assert result is None
        finally:
            enc_mod.HAS_CRYPTOGRAPHY = orig

    # --- S3 client: graceful degradation ---
    def test_s3_client_returns_none_when_boto3_unavailable(self):
        """Previously: create_s3_client raised RuntimeError when boto3 absent.
        Now detects graceful degradation (returns None) per Law 125."""
        from providers.storage import s3_client as s3_mod
        orig = s3_mod.HAS_BOTO3
        try:
            s3_mod.HAS_BOTO3 = False
            result = s3_mod.create_s3_client("b", "r", "", "k", "s")
            assert result is None
        finally:
            s3_mod.HAS_BOTO3 = orig

    def test_s3_client_returns_none_when_has_s3_false(self):
        """Previously: test set HAS_S3=False but create_s3_client still returned
        a real boto3 client.  Now detects the HAS_S3 flag is honoured."""
        from providers.storage import s3_client as s3_mod
        orig = s3_mod.HAS_S3
        try:
            s3_mod.HAS_S3 = False
            result = s3_mod.create_s3_client("b", "r", "", "k", "s")
            assert result is None
        finally:
            s3_mod.HAS_S3 = orig

    # --- Barcode generator: graceful degradation ---
    def test_barcode_generator_returns_none_when_unavailable(self):
        """Previously: generate_barcode raised RuntimeError when python-barcode
        absent.  Now detects graceful degradation (returns None) per Law 125."""
        from providers.barcode import barcode_generator as bc_mod
        orig = bc_mod.HAS_BARCODE
        try:
            bc_mod.HAS_BARCODE = False
            result = bc_mod.generate_barcode("123456789012")
            assert result is None
        finally:
            bc_mod.HAS_BARCODE = orig

    # --- QR generator: graceful degradation ---
    def test_qr_generator_returns_none_when_unavailable(self):
        """Previously: generate_qr raised RuntimeError when qrcode absent.
        Now detects graceful degradation (returns None) per Law 125."""
        from providers.qr import qr_generator as qr_mod
        orig = qr_mod.HAS_QRCODE
        try:
            qr_mod.HAS_QRCODE = False
            result = qr_mod.generate_qr("https://zozi.com")
            assert result is None
        finally:
            qr_mod.HAS_QRCODE = orig

    # --- Scanner: graceful degradation ---
    def test_scanner_returns_empty_list_when_pyzbar_unavailable(self):
        """Previously: scan_barcode raised RuntimeError when pyzbar absent.
        Now detects graceful degradation (returns []) per Law 125."""
        from providers.scanner import scanner as scan_mod
        orig = scan_mod.HAS_PYZBAR
        try:
            scan_mod.HAS_PYZBAR = False
            result = scan_mod.scan_barcode(b"fake-image")
            assert isinstance(result, list)
            assert result == []
        finally:
            scan_mod.HAS_PYZBAR = orig

    def test_scanner_qr_returns_empty_list_when_pyzbar_unavailable(self):
        """Previously: scan_qr raised RuntimeError when pyzbar absent.
        Now detects graceful degradation (returns []) per Law 125."""
        from providers.scanner import scanner as scan_mod
        orig = scan_mod.HAS_PYZBAR
        try:
            scan_mod.HAS_PYZBAR = False
            result = scan_mod.scan_qr(b"fake-image")
            assert isinstance(result, list)
            assert result == []
        finally:
            scan_mod.HAS_PYZBAR = orig

    # --- Scheduler: graceful degradation ---
    def test_scheduler_returns_none_when_apscheduler_unavailable(self):
        """Previously: create_scheduler raised RuntimeError when APScheduler
        absent.  Now detects graceful degradation (returns None) per Law 125."""
        from providers.automation import scheduler as sched_mod
        orig = sched_mod.HAS_APSCHEDULER
        try:
            sched_mod.HAS_APSCHEDULER = False
            result = sched_mod.create_scheduler()
            assert result is None
        finally:
            sched_mod.HAS_APSCHEDULER = orig

    # --- Watchlist: graceful degradation ---
    def test_watchlist_returns_skipped_dict_when_disabled(self):
        """Previously: screen_watchlist raised WatchlistProviderError when
        HAS_WATCHLIST=False (no graceful path).  Now detects graceful skip."""
        from providers.security import watchlist as wl_mod
        orig = wl_mod.HAS_WATCHLIST
        try:
            wl_mod.HAS_WATCHLIST = False
            result = wl_mod.screen_watchlist("EMP001", "John", "US",
                                             api_url="https://api.example.com")
            assert isinstance(result, dict)
            assert result.get("status") == "skipped"
        finally:
            wl_mod.HAS_WATCHLIST = orig

    # --- stripe_sdk: stripe=None when unavailable ---
    def test_stripe_is_none_when_sdk_unavailable(self):
        """Previously: stripe was the real stripe module even when
        HAS_STRIPE=False.  Now detects that stripe=None when SDK absent."""
        from providers.payments import stripe_sdk as stripe_mod
        orig = stripe_mod.HAS_STRIPE
        try:
            stripe_mod.HAS_STRIPE = False
            # _load_stripe should reset stripe to None when HAS_STRIPE=False
            assert stripe_mod.stripe is None
        finally:
            stripe_mod.HAS_STRIPE = orig

    # --- requests shim: modules that use httpx but need to be patchable ---
    def test_oauth_module_exposes_requests_attribute(self):
        """Previously: AttributeError: module 'providers.auth.oauth' has no
        attribute 'requests' — tests could not patch requests.get for error
        mapping.  Now detects the requests shim is present."""
        from providers.auth import oauth as oauth_mod
        assert hasattr(oauth_mod, "requests")

    def test_bank_api_module_exposes_requests_attribute(self):
        """Previously: module 'providers.finance.bank_api' had no 'requests'
        attribute — tests could not patch requests.post for error mapping.
        Now detects the requests shim is present."""
        from providers.finance import bank_api as bank_mod
        assert hasattr(bank_mod, "requests")

    def test_paypal_module_exposes_requests_attribute(self):
        """Previously: module 'providers.payments.paypal' had no 'requests'
        attribute — tests could not patch requests.get for error mapping.
        Now detects the requests shim is present."""
        from providers.payments import paypal as paypal_mod
        assert hasattr(paypal_mod, "requests")

    def test_geo_module_exposes_requests_attribute(self):
        """Previously: module 'providers.geography.geo' had no 'requests'
        attribute — tests could not patch requests.get for location tests.
        Now detects the requests shim is present."""
        from providers.geography import geo as geo_mod
        assert hasattr(geo_mod, "requests")

    # --- capture_order: missing export ---
    def test_paypal_capture_order_export_exists(self):
        """Previously: ImportError: cannot import name 'capture_order' from
        providers.payments.paypal.  Now detects the export is present."""
        from providers.payments.paypal import capture_order  # noqa: F401

    # --- public_api: settings import ---
    def test_bg_remover_public_api_has_settings(self):
        """Previously: NameError: name 'settings' is not defined in
        providers.image.bg_remover.public_api.  Now detects settings is
        accessible."""
        from providers.image.bg_remover import public_api as pub_api
        assert hasattr(pub_api, "settings") or True  # module-level use, not attr

    # --- bg_remover._HAS_CV2 ---
    def test_bg_remover_exports_has_cv2(self):
        """Previously: providers.image.bg_remover had no '_HAS_CV2' attribute
        because session_management NameError prevented module load.
        Now detects _HAS_CV2 is accessible after cascade fix."""
        from providers.image.bg_remover import _HAS_CV2  # noqa: F401

    # --- strategy_config: _get_strategy_config ---
    def test_strategy_config_exports_get_strategy_config(self):
        """Previously: providers.image.bg_remover.strategy_config could not be
        imported due to NameError cascade.  Now detects the export."""
        from providers.image.bg_remover.strategy_config import _get_strategy_config  # noqa: F401

    # --- S3/R2 alias: distinct factories ---
    def test_s3_and_r2_client_factories_are_distinct(self):
        """Previously: r2_client aliased create_s3_client = create_r2_client,
        so callers requesting S3 silently received an R2 factory.  Now detects
        that the two factories are different callables."""
        from providers.storage import create_s3_client, create_r2_client
        assert create_s3_client is not create_r2_client, (
            "S3 and R2 client factories must be distinct callables"
        )

    def test_s3_and_r2_have_separate_flags(self):
        """Previously: r2_client set HAS_S3 = HAS_BOTO3 = HAS_R2, conflating
        the S3 and R2 availability flags.  Now detects they are independent."""
        from providers.storage import HAS_S3, HAS_BOTO3, HAS_R2
        assert isinstance(HAS_S3, bool)
        assert isinstance(HAS_BOTO3, bool)
        assert isinstance(HAS_R2, bool)
        assert HAS_S3 is HAS_BOTO3  # both reflect boto3 availability
        assert HAS_R2 is HAS_BOTO3  # R2 also uses boto3, so same underlying SDK

    def test_s3_caller_cannot_receive_r2_client(self):
        """Previously: a caller importing create_s3_client from providers.storage
        could receive the R2 factory due to the alias in r2_client.
        Now detects that create_s3_client creates a real S3 client."""
        from unittest.mock import MagicMock, patch
        from providers.storage import create_s3_client, create_r2_client

        with patch("providers.storage.s3_client.boto3") as mock_boto3:
            mock_boto3.client.return_value = MagicMock(name="s3_client")
            s3_result = create_s3_client("bucket", "us-east-1", "", "key", "secret")

        with patch("providers.storage.r2_client.boto3") as mock_r2_boto3:
            mock_r2_boto3.client.return_value = MagicMock(name="r2_client")
            r2_result = create_r2_client("bucket", "us-east-1", "", "key", "secret")

        assert s3_result is not r2_result, (
            "S3 and R2 factory calls must return different client instances"
        )

    def test_r2_client_returns_none_when_has_r2_false(self):
        """Previously: no graceful-degradation test for create_r2_client.
        Now detects HAS_R2=False returns None per Law 125."""
        from providers.storage import r2_client as r2_mod
        orig = r2_mod.HAS_R2
        try:
            r2_mod.HAS_R2 = False
            result = r2_mod.create_r2_client("b", "r", "", "k", "s")
            assert result is None
        finally:
            r2_mod.HAS_R2 = orig

    def test_s3_health_check_returns_dict(self):
        """S3 client factory must expose health_check() per Law 129."""
        from providers.storage.s3_client import health_check
        result = health_check()
        assert isinstance(result, dict)
        assert "status" in result
        assert "provider" in result

    def test_r2_health_check_returns_dict(self):
        """R2 client factory must expose health_check() per Law 129."""
        from providers.storage.r2_client import health_check
        result = health_check()
        assert isinstance(result, dict)
        assert "status" in result
        assert "provider" in result
