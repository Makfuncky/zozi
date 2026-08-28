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

    def test_redis_health_status_callable(self):
        from infrastructure.utils.auth import get_redis_health_status
        result = get_redis_health_status()
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
