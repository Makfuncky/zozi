"""Comprehensive functional test suite for ALL provider tools.

Verifies each provider works with REAL inputs (not just imports).
Tests are organized by provider domain and skip gracefully when optional
dependencies are missing.

Run: python -m pytest backend/tests/providers/test_functional_providers.py -v
"""

from __future__ import annotations

import base64
import csv
import io
import json
import math
import os
import tempfile
from decimal import Decimal
from typing import Any, Dict, List, Optional

import pytest


# ═══════════════════════════════════════════════════════════════════
# 1. IMAGE PROCESSING (providers/image/free_image_tools.py)
# ═══════════════════════════════════════════════════════════════════

class TestImageProcessingTools:
    """Test free_image_tools with real PIL image bytes."""

    @pytest.fixture
    def sample_image_bytes(self) -> bytes:
        """Create a real 100x100 RGB image and return its bytes."""
        try:
            from PIL import Image
        except ImportError:
            pytest.skip("Pillow not installed")

        img = Image.new("RGB", (100, 100), color=(255, 0, 0))
        # Draw some non-uniform content so crop/erase have something to work with
        for x in range(25, 75):
            for y in range(25, 75):
                img.putpixel((x, y), (0, 128, 255))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    @pytest.fixture
    def sample_jpeg_bytes(self) -> bytes:
        """Create a real 100x100 JPEG image."""
        try:
            from PIL import Image
        except ImportError:
            pytest.skip("Pillow not installed")

        img = Image.new("RGB", (100, 100), color=(0, 128, 0))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85)
        return buf.getvalue()

    def test_magic_erase_returns_bytes(self, sample_image_bytes):
        from providers.image.free_image_tools import magic_erase
        result = magic_erase(sample_image_bytes)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_smart_crop_returns_bytes(self, sample_image_bytes):
        from providers.image.free_image_tools import smart_crop
        result = smart_crop(sample_image_bytes, target_ratio=1.0, padding=0.08)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_smart_crop_with_ratio(self, sample_image_bytes):
        from providers.image.free_image_tools import smart_crop
        result = smart_crop(sample_image_bytes, target_ratio=1.5, padding=0.1)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_auto_rotate_returns_bytes(self, sample_image_bytes):
        from providers.image.free_image_tools import auto_rotate
        result = auto_rotate(sample_image_bytes, angle=0)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_auto_rotate_with_angle(self, sample_image_bytes):
        from providers.image.free_image_tools import auto_rotate
        result = auto_rotate(sample_image_bytes, angle=90)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_auto_lighting_returns_bytes(self, sample_image_bytes):
        from providers.image.free_image_tools import auto_lighting
        result = auto_lighting(sample_image_bytes, clip_limit=2.0, brightness=1.05)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_upscale_returns_bytes(self, sample_image_bytes):
        from providers.image.free_image_tools import upscale
        result = upscale(sample_image_bytes, scale=2.0, method="lanczos")
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_upscale_cubic(self, sample_image_bytes):
        from providers.image.free_image_tools import upscale
        result = upscale(sample_image_bytes, scale=1.5, method="cubic")
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_auto_white_balance_returns_bytes(self, sample_image_bytes):
        from providers.image.free_image_tools import auto_white_balance
        result = auto_white_balance(sample_image_bytes, strength=0.5)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_sharpen_returns_bytes(self, sample_image_bytes):
        from providers.image.free_image_tools import sharpen
        result = sharpen(sample_image_bytes, strength=1.0)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_compress_returns_bytes(self, sample_image_bytes):
        from providers.image.free_image_tools import compress
        result = compress(sample_image_bytes, quality=80)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_webp_convert_returns_bytes(self, sample_image_bytes):
        from providers.image.free_image_tools import webp_convert
        result = webp_convert(sample_image_bytes, quality=85)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_color_enhance_returns_bytes(self, sample_image_bytes):
        from providers.image.free_image_tools import color_enhance
        result = color_enhance(sample_image_bytes, saturation=1.15)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_auto_levels_returns_bytes(self, sample_image_bytes):
        from providers.image.free_image_tools import auto_levels
        result = auto_levels(sample_image_bytes, clip_hist=0.5)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_auto_process_image_pipeline(self, sample_image_bytes):
        from providers.image.free_image_tools import auto_process_image
        result = auto_process_image(
            sample_image_bytes,
            tools=["auto_lighting", "sharpen", "compress"],
        )
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_auto_process_image_full_pipeline(self, sample_image_bytes):
        from providers.image.free_image_tools import auto_process_image
        result = auto_process_image(
            sample_image_bytes,
            tools=["white_balance", "color_enhance", "auto_levels", "sharpen", "compress"],
        )
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_jpeg_input_compress(self, sample_jpeg_bytes):
        from providers.image.free_image_tools import compress
        result = compress(sample_jpeg_bytes, quality=50)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_tool_registry_has_all_tools(self):
        from providers.image.free_image_tools import TOOL_REGISTRY
        expected = [
            "magic_erase", "smart_crop", "rotate", "auto_light", "upscale",
            "white_balance", "denoise", "sharpen", "compress", "webp_convert",
            "color_enhance", "auto_levels",
        ]
        for tool in expected:
            assert tool in TOOL_REGISTRY, f"Missing tool: {tool}"


# ═══════════════════════════════════════════════════════════════════
# 2. OCR (providers/ocr/ocr_parser.py)
# ═══════════════════════════════════════════════════════════════════

class TestOCRParser:
    """Test OCR parser with real text inputs."""

    def test_parse_bill_text_full_receipt(self):
        from providers.ocr.ocr_parser import parse_bill_text
        receipt = """ABC Trading LLC
123 Main Street, Muscat
Date: 2024-03-15
Bill #:INV-2024-001
Item 1: Office Supplies    25.50
Item 2: Printer Paper       8.75
VAT: 1.71
Grand Total:                35.96 OMR"""
        result = parse_bill_text(receipt)
        assert result["vendor_name"] == "ABC Trading LLC"
        assert result["amount"] == Decimal("35.96")
        assert result["tax_amount"] == Decimal("1.71")
        assert result["expense_date"] == "2024-03-15"
        assert result["invoice_number"] == "INV-2024-001"
        assert result["confidence"] >= 0.85

    def test_parse_bill_text_minimal(self):
        from providers.ocr.ocr_parser import parse_bill_text
        result = parse_bill_text("Cafe Restaurant\nTotal: 12.500")
        assert result["vendor_name"] == "Cafe Restaurant"
        assert result["amount"] == Decimal("12.500")

    def test_parse_bill_text_empty(self):
        from providers.ocr.ocr_parser import parse_bill_text
        result = parse_bill_text("")
        assert result["vendor_name"] is None
        assert result["amount"] is None
        assert result["confidence"] == 0.0

    def test_parse_bill_text_with_filename_fallback(self):
        from providers.ocr.ocr_parser import parse_bill_text
        result = parse_bill_text("", filename="inv-999.png")
        assert result["invoice_number"] == "999"
        assert result["confidence"] == 0.15

    def test_parse_bill_text_amount_excludes_years(self):
        from providers.ocr.ocr_parser import parse_bill_text
        receipt = """Tech Solutions Ltd
Date: 2024-01-15
Total: 150.000 OMR"""
        result = parse_bill_text(receipt)
        assert result["amount"] == Decimal("150.000")

    def test_parse_statement_csv_standard(self):
        from providers.ocr.ocr_parser import parse_statement_csv
        csv_data = """Date,Description,Amount,Reference
2024-01-15,Supplier Payment,-500.00,REF001
2024-01-16,Customer Deposit,1200.50,REF002
2024-01-17,Office Rent,-300.00,REF003"""
        result = parse_statement_csv(csv_data)
        assert len(result) == 3
        assert result[0]["description"] == "Supplier Payment"
        assert result[0]["amount"] == -500.00
        assert result[0]["txn_date"] == "2024-01-15"
        assert result[1]["amount"] == 1200.50

    def test_parse_statement_csv_no_header(self):
        from providers.ocr.ocr_parser import parse_statement_csv
        csv_data = """2024-01-15,Supplier Payment,-500.00
2024-01-16,Customer Deposit,1200.50"""
        result = parse_statement_csv(csv_data)
        assert len(result) == 2
        assert result[0]["amount"] == -500.00

    def test_parse_statement_csv_empty(self):
        from providers.ocr.ocr_parser import parse_statement_csv
        result = parse_statement_csv("")
        assert result == []

    def test_parse_bill_text_different_date_formats(self):
        from providers.ocr.ocr_parser import parse_bill_text
        receipt = """Store Ltd
Date: 15/03/2024
Total: 45.000"""
        result = parse_bill_text(receipt)
        assert result["expense_date"] == "2024-03-15"

    def test_parse_bill_text_vendor_hints(self):
        from providers.ocr.ocr_parser import parse_bill_text
        receipt = """Global Tech Solutions
Some items here
Total: 99.990"""
        result = parse_bill_text(receipt)
        assert result["vendor_name"] == "Global Tech Solutions"


# ═══════════════════════════════════════════════════════════════════
# 3. BG REMOVAL (providers/bg_removal/bg_removal_service.py)
# ═══════════════════════════════════════════════════════════════════

class TestBGRemovalService:
    """Test bg_removal_service module structure and graceful degradation."""

    def test_module_imports(self):
        from providers.bg_removal import bg_removal_service
        assert hasattr(bg_removal_service, "remove_background")
        assert hasattr(bg_removal_service, "magic_erase")
        assert hasattr(bg_removal_service, "_SessionManager")
        assert hasattr(bg_removal_service, "CleanEdgeRefiner")

    def test_available_models_is_list(self):
        from providers.bg_removal.bg_removal_service import AVAILABLE_MODELS
        assert isinstance(AVAILABLE_MODELS, list)
        assert len(AVAILABLE_MODELS) > 0

    def test_valid_strategies_exist(self):
        from providers.bg_removal.bg_removal_service import VALID_STRATEGIES
        assert "auto" in VALID_STRATEGIES
        assert "clean_commercial" in VALID_STRATEGIES
        assert "lite_variants" in VALID_STRATEGIES

    def test_remove_background_returns_original_on_failure(self):
        """When models are missing, should return data unchanged."""
        from providers.bg_removal.bg_removal_service import remove_background
        dummy_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        result = remove_background(dummy_bytes, strategy="auto")
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_magic_erase_returns_bytes(self):
        from providers.bg_removal.bg_removal_service import magic_erase
        dummy_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        result = magic_erase(dummy_bytes)
        assert isinstance(result, bytes)

    def test_session_manager_clear_all(self):
        from providers.bg_removal.bg_removal_service import _SessionManager
        _SessionManager.clear_all()
        assert len(_SessionManager._sessions) == 0

    def test_remove_background_preset_returns_bytes(self):
        from providers.bg_removal.bg_removal_service import remove_background_preset
        dummy_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        result = remove_background_preset(dummy_bytes, preset="general")
        assert isinstance(result, bytes)

    def test_compute_quality_score(self):
        """Test the quality scoring function with a real alpha array."""
        import numpy as np
        from providers.bg_removal.bg_removal_service import _compute_quality_score
        img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        alpha = np.zeros((100, 100), dtype=np.float32)
        alpha[25:75, 25:75] = 1.0
        score = _compute_quality_score(img, alpha)
        assert "edge_clarity" in score
        assert "alpha_confidence" in score
        assert "coverage" in score
        assert "overall" in score
        assert 0 <= score["overall"] <= 1

    def test_detect_category(self):
        """Test category detection with a real image array."""
        try:
            import cv2  # noqa: F401
        except ImportError:
            pytest.skip("OpenCV not installed")
        import numpy as np
        from providers.bg_removal.bg_removal_service import _detect_category
        img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        category = _detect_category(img)
        assert category in ("clothing", "electronics", "beauty", "unknown")


# ═══════════════════════════════════════════════════════════════════
# 4. AUTH (providers/auth/)
# ═══════════════════════════════════════════════════════════════════

class TestAuthProviders:
    """Test JWT, TOTP, Apple auth providers with real inputs."""

    def test_jwt_decode_token(self):
        from jose import jwt as _jose_jwt
        from providers.auth.jwt import decode_token
        secret = "test-secret-key-for-functional-test"
        payload = {"sub": "user123", "role": "admin", "jti": "test-jti-001"}
        token = _jose_jwt.encode(payload, secret, algorithm="HS256")
        result = decode_token(token, secret, algorithms=["HS256"])
        assert result["sub"] == "user123"
        assert result["role"] == "admin"
        assert result["jti"] == "test-jti-001"

    def test_jwt_decode_unverified_claims(self):
        from jose import jwt as _jose_jwt
        from providers.auth.jwt import decode_unverified_claims
        payload = {"sub": "user456", "role": "customer"}
        token = _jose_jwt.encode(payload, "any-secret", algorithm="HS256")
        claims = decode_unverified_claims(token)
        assert claims["sub"] == "user456"

    def test_totp_generate_secret(self):
        from providers.auth.totp import generate_secret
        secret = generate_secret()
        assert isinstance(secret, str)
        assert len(secret) > 0

    def test_totp_verify_valid_code(self):
        import pyotp
        from providers.auth.totp import generate_secret, verify
        secret = generate_secret()
        totp = pyotp.TOTP(secret)
        current_code = totp.now()
        assert verify(secret, current_code) is True

    def test_totp_verify_invalid_code(self):
        from providers.auth.totp import generate_secret, verify
        secret = generate_secret()
        assert verify(secret, "000000") is False

    def test_totp_verify_empty_inputs(self):
        from providers.auth.totp import verify
        assert verify("", "123456") is False
        assert verify("secret", "") is False

    def test_totp_provisioning_uri(self):
        from providers.auth.totp import generate_secret, provisioning_uri
        secret = generate_secret()
        uri = provisioning_uri(secret, name="user@example.com", issuer_name="Zozi")
        assert uri.startswith("otpauth://")
        assert "Zozi" in uri

    def test_apple_build_auth_url(self):
        from providers.auth.apple import build_apple_auth_url
        url = build_apple_auth_url(
            client_id="com.zozi.app",
            redirect_uri="https://zozi.com/auth/callback",
            state="random-state-123",
        )
        assert url.startswith("https://appleid.apple.com/auth/authorize")
        assert "client_id=com.zozi.app" in url
        assert "redirect_uri=" in url
        assert "state=random-state-123" in url
        assert "response_type=code" in url

    def test_apple_build_auth_url_with_scope(self):
        from providers.auth.apple import build_apple_auth_url
        url = build_apple_auth_url(
            client_id="com.zozi.app",
            redirect_uri="https://zozi.com/auth/callback",
            state="s1",
            scope="name email",
        )
        assert "scope=name+email" in url or "scope=name%20email" in url


# ═══════════════════════════════════════════════════════════════════
# 5. GEOGRAPHY (providers/geography/)
# ═══════════════════════════════════════════════════════════════════

class TestGeographyProviders:
    """Test geography IP and rate providers."""

    def test_detect_country_from_ip_private(self):
        from providers.geography.ip import detect_country_from_ip
        result = detect_country_from_ip("192.168.1.1")
        assert result is None

    def test_detect_country_from_ip_loopback(self):
        from providers.geography.ip import detect_country_from_ip
        result = detect_country_from_ip("127.0.0.1")
        assert result is None

    def test_detect_country_from_ip_empty(self):
        from providers.geography.ip import detect_country_from_ip
        result = detect_country_from_ip("")
        assert result is None

    def test_detect_country_from_ip_invalid(self):
        from providers.geography.ip import detect_country_from_ip
        result = detect_country_from_ip("not-an-ip")
        assert result is None

    def test_geocode_location_returns_none_without_network(self):
        from providers.geography.ip import geocode_location
        result = geocode_location("Muscat", timeout=0.001)
        assert result is None or isinstance(result, list)

    def test_normalize_currency_code(self):
        from providers.geography.rates import normalize_currency_code
        assert normalize_currency_code("usd") == "USD"
        assert normalize_currency_code("OMR") == "OMR"
        assert normalize_currency_code(None, default="OMR") == "OMR"
        assert normalize_currency_code("US Dollar", default="OMR") == "OMR"

    def test_fetch_rates_returns_tuple(self):
        from providers.geography.rates import fetch_rates
        rates, source = fetch_rates()
        assert isinstance(rates, dict)
        assert source in ("live", "fallback")

    def test_reset_rate_cache(self):
        from providers.geography.rates import reset_rate_cache, rate_cache_expiry
        reset_rate_cache()
        assert rate_cache_expiry() == 0.0

    def test_country_detection_provider_class(self):
        from providers.geography.geo import CountryDetectionProvider
        provider = CountryDetectionProvider()
        assert hasattr(provider, "detect_country_from_ip")
        assert hasattr(provider, "get_country_details")

    def test_country_detection_private_ip(self):
        from providers.geography.geo import CountryDetectionProvider
        provider = CountryDetectionProvider()
        code, source = provider.detect_country_from_ip({}, client_host="192.168.1.1")
        assert source == "private"

    def test_country_detection_no_ip(self):
        from providers.geography.geo import CountryDetectionProvider
        provider = CountryDetectionProvider()
        code, source = provider.detect_country_from_ip({})
        assert source == "unknown"

    def test_get_country_details(self):
        from providers.geography.geo import CountryDetectionProvider
        provider = CountryDetectionProvider()
        details = provider.get_country_details("US")
        assert details["code"] == "US"
        assert "currency" in details

    def test_ip_location_dataclass(self):
        from providers.geography.geo import IpLocation
        loc = IpLocation(ip="8.8.8.8", country="US", country_code="US")
        d = loc.to_dict()
        assert d["ip"] == "8.8.8.8"
        assert d["country_code"] == "US"

    def test_reverse_location_dataclass(self):
        from providers.geography.geo import ReverseLocation
        loc = ReverseLocation(latitude=23.588, longitude=58.384, display_name="Muscat")
        d = loc.to_dict()
        assert d["latitude"] == 23.588
        assert d["display_name"] == "Muscat"


# ═══════════════════════════════════════════════════════════════════
# 6. STORAGE (providers/storage/)
# ═══════════════════════════════════════════════════════════════════

class TestStorageProviders:
    """Test storage backends with real temp directories."""

    def test_local_storage_save_and_read(self):
        from providers.storage.storage_backend import LocalStorage
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalStorage(base_dir=tmpdir)
            url = storage.save("test/image.png", b"fake-image-data")
            assert url == "/uploads/test/image.png"
            data = storage.read("test/image.png")
            assert data == b"fake-image-data"

    def test_local_storage_url(self):
        from providers.storage.storage_backend import LocalStorage
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalStorage(base_dir=tmpdir)
            assert storage.url("test/file.txt") == "/uploads/test/file.txt"

    def test_local_storage_delete(self):
        from providers.storage.storage_backend import LocalStorage
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalStorage(base_dir=tmpdir)
            storage.save("to_delete.txt", b"data")
            storage.delete("to_delete.txt")
            # Should not raise
            storage.delete("nonexistent.txt")

    def test_local_storage_list(self):
        from providers.storage.storage_backend import LocalStorage
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalStorage(base_dir=tmpdir)
            storage.save("a/1.txt", b"1")
            storage.save("a/2.txt", b"2")
            storage.save("b/3.txt", b"3")
            all_files = storage.list()
            assert len(all_files) == 3
            a_files = storage.list(prefix="a/")
            assert len(a_files) == 2

    def test_local_storage_path_traversal_protection(self):
        from providers.storage.storage_backend import LocalStorage
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalStorage(base_dir=tmpdir)
            with pytest.raises(ValueError):
                storage.read("../../etc/passwd")

    def test_create_s3_client_raises_import_error_without_boto3(self):
        """If boto3 is not installed, create_s3_client raises ImportError."""
        from providers.storage import create_s3_client
        try:
            import boto3  # noqa: F401
            pytest.skip("boto3 is installed, cannot test ImportError path")
        except ImportError:
            with pytest.raises(ImportError):
                create_s3_client("bucket", "us-east-1", "", "key", "secret")

    def test_storage_backend_is_abstract(self):
        from providers.storage.storage_backend import StorageBackend
        with pytest.raises(TypeError):
            StorageBackend()


# ═══════════════════════════════════════════════════════════════════
# 7. PAYMENTS (providers/payments/)
# ═══════════════════════════════════════════════════════════════════

class TestPaymentProviders:
    """Test payment gateway providers."""

    def test_stripe_has_stripe_is_boolean(self):
        from providers.payments.stripe_sdk import HAS_STRIPE
        assert isinstance(HAS_STRIPE, bool)

    def test_paypal_is_available_is_boolean(self):
        from providers.payments.paypal import is_available
        assert isinstance(is_available(), bool)

    def test_paypal_has_paypal_is_boolean(self):
        from providers.payments.paypal import HAS_PAYPAL
        assert isinstance(HAS_PAYPAL, bool)

    def test_registry_register_and_get(self):
        from providers.payments.registry import PaymentGatewayRegistry
        from providers.payments.base import BasePaymentGateway

        class DummyGateway(BasePaymentGateway):
            pass

        PaymentGatewayRegistry.register("dummy_test", DummyGateway)
        assert PaymentGatewayRegistry.get("dummy_test") is DummyGateway
        PaymentGatewayRegistry.unregister("dummy_test")
        assert PaymentGatewayRegistry.get("dummy_test") is None

    def test_registry_get_or_raise(self):
        from providers.payments.registry import PaymentGatewayRegistry
        from providers.payments.base import BasePaymentGateway

        class DummyGateway2(BasePaymentGateway):
            pass

        PaymentGatewayRegistry.register("dummy_test2", DummyGateway2)
        try:
            with pytest.raises(KeyError):
                PaymentGatewayRegistry.get_or_raise("nonexistent")
            assert PaymentGatewayRegistry.get_or_raise("dummy_test2") is DummyGateway2
        finally:
            PaymentGatewayRegistry.unregister("dummy_test2")

    def test_registry_list_available(self):
        from providers.payments.registry import PaymentGatewayRegistry
        from providers.payments.base import BasePaymentGateway

        class DummyGateway3(BasePaymentGateway):
            pass

        PaymentGatewayRegistry.register("zzz_test", DummyGateway3)
        try:
            available = PaymentGatewayRegistry.list_available()
            assert "zzz_test" in available
        finally:
            PaymentGatewayRegistry.unregister("zzz_test")

    def test_registry_register_adapter_decorator(self):
        from providers.payments.registry import PaymentGatewayRegistry
        from providers.payments.base import BasePaymentGateway

        @PaymentGatewayRegistry.register_adapter("decorated_test")
        class DecoratedGateway(BasePaymentGateway):
            pass

        assert PaymentGatewayRegistry.get("decorated_test") is DecoratedGateway
        PaymentGatewayRegistry.unregister("decorated_test")

    def test_registry_clear(self):
        from providers.payments.registry import PaymentGatewayRegistry
        from providers.payments.base import BasePaymentGateway

        class DummyGateway4(BasePaymentGateway):
            pass

        PaymentGatewayRegistry.register("clear_test", DummyGateway4)
        PaymentGatewayRegistry.clear()
        assert PaymentGatewayRegistry.list_available() == []

    def test_paypal_error_classes_exist(self):
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


# ═══════════════════════════════════════════════════════════════════
# 8. COMMS (providers/comms/)
# ═══════════════════════════════════════════════════════════════════

class TestCommsProviders:
    """Test email and Twilio providers."""

    def test_deliver_email_console_mode(self):
        from providers.comms.email import deliver_email
        # Console mode should work without SMTP
        result = deliver_email(
            to="test@example.com",
            subject="Test Subject",
            html="<h1>Hello</h1>",
            from_address="noreply@zozi.com",
            provider="console",
        )
        assert result is None

    def test_deliver_email_disabled_raises(self):
        from providers.comms.email import deliver_email
        with pytest.raises(RuntimeError):
            deliver_email(
                to="test@example.com",
                subject="Test",
                html="<p>Test</p>",
                from_address="noreply@zozi.com",
                provider="unknown_provider",
            )

    def test_twilio_has_twilio_is_boolean(self):
        from providers.comms.twilio import HAS_TWILIO
        assert isinstance(HAS_TWILIO, bool)

    def test_twilio_create_client_returns_none_when_unavailable(self):
        from providers.comms.twilio import create_twilio_client, HAS_TWILIO
        if not HAS_TWILIO:
            result = create_twilio_client("sid", "token")
            assert result is None


# ═══════════════════════════════════════════════════════════════════
# 9. AI (providers/ai/)
# ═══════════════════════════════════════════════════════════════════

class TestAIProviders:
    """Test AI text and search providers."""

    def test_extract_json_valid_object(self):
        from providers.ai.text import _extract_json
        result = _extract_json('{"name": "test", "value": 42}')
        assert result == {"name": "test", "value": 42}

    def test_extract_json_valid_array(self):
        from providers.ai.text import _extract_json
        result = _extract_json('[1, 2, 3]')
        assert result == [1, 2, 3]

    def test_extract_json_with_surrounding_text(self):
        from providers.ai.text import _extract_json
        text = 'Here is the result: {"status": "ok", "count": 5} and more text'
        result = _extract_json(text)
        assert result == {"status": "ok", "count": 5}

    def test_extract_json_with_code_fences(self):
        from providers.ai.text import _extract_json
        text = '```json\n{"key": "value"}\n```'
        result = _extract_json(text)
        assert result == {"key": "value"}

    def test_extract_json_invalid_returns_none(self):
        from providers.ai.text import _extract_json
        result = _extract_json("no json here at all")
        assert result is None

    def test_extract_json_fixes_single_quotes(self):
        from providers.ai.text import _extract_json
        result = _extract_json("{'key': 'value'}")
        assert result == {"key": "value"}

    def test_extract_json_fixes_trailing_commas(self):
        from providers.ai.text import _extract_json
        result = _extract_json('{"a": 1, "b": 2,}')
        assert result == {"a": 1, "b": 2}

    def test_cosine_similarity_identical_vectors(self):
        from providers.ai.text import cosine_similarity
        vec = [1.0, 2.0, 3.0]
        result = cosine_similarity(vec, vec)
        assert abs(result - 1.0) < 1e-9

    def test_cosine_similarity_orthogonal_vectors(self):
        from providers.ai.text import cosine_similarity
        a = [1.0, 0.0, 0.0]
        b = [0.0, 1.0, 0.0]
        result = cosine_similarity(a, b)
        assert abs(result) < 1e-9

    def test_cosine_similarity_different_length(self):
        from providers.ai.text import cosine_similarity
        result = cosine_similarity([1.0, 2.0], [1.0])
        assert result == 0.0

    def test_cosine_similarity_empty_vectors(self):
        from providers.ai.text import cosine_similarity
        assert cosine_similarity([], []) == 0.0
        assert cosine_similarity([1.0], []) == 0.0

    def test_advanced_search_engine_instantiation(self):
        from providers.ai.search import AdvancedSearchEngine
        engine = AdvancedSearchEngine()
        assert hasattr(engine, "parse_query")
        assert hasattr(engine, "search")
        assert hasattr(engine, "fuzzy_search")

    def test_advanced_search_engine_parse_query(self):
        from providers.ai.search import AdvancedSearchEngine
        engine = AdvancedSearchEngine()
        result = engine.parse_query("red shoes under 50 size M")
        assert result["color"] == "red"
        assert result["max_price"] == 50.0
        assert result["size"] == "M"

    def test_advanced_search_engine_parse_query_sort(self):
        from providers.ai.search import AdvancedSearchEngine
        engine = AdvancedSearchEngine()
        result = engine.parse_query("cheapest laptops")
        assert result["sort"] == "price_asc"

    def test_advanced_search_engine_parse_query_category(self):
        from providers.ai.search import AdvancedSearchEngine
        engine = AdvancedSearchEngine()
        result = engine.parse_query("smart watch with video")
        assert result["category"] == "electronics"

    def test_advanced_search_engine_search(self):
        from providers.ai.search import AdvancedSearchEngine
        engine = AdvancedSearchEngine()
        result = engine.search("test query")
        assert "products" in result
        assert "parsed_query" in result

    def test_advanced_search_engine_load_catalog(self):
        from providers.ai.search import AdvancedSearchEngine
        engine = AdvancedSearchEngine()
        products = [
            {"id": 1, "name": "Red Shoe", "description": "A red shoe", "tags": ["shoe", "red"]},
        ]
        count = engine.load_product_catalog(products)
        assert count == 1


# ═══════════════════════════════════════════════════════════════════
# 10. AUTOMATION (providers/automation/)
# ═══════════════════════════════════════════════════════════════════

class TestAutomationProviders:
    """Test automation scheduler provider."""

    def test_create_scheduler(self):
        from providers.automation.scheduler import create_scheduler
        scheduler = create_scheduler()
        assert scheduler is not None

    def test_create_scheduler_with_timezone(self):
        from providers.automation.scheduler import create_scheduler
        scheduler = create_scheduler(timezone="UTC")
        assert scheduler is not None

    def test_add_interval_job(self):
        from providers.automation.scheduler import create_scheduler, add_interval_job
        scheduler = create_scheduler()

        def dummy_job():
            pass

        add_interval_job(scheduler, dummy_job, seconds=60, id="test_job")
        jobs = scheduler.get_jobs()
        assert len(jobs) == 1
        assert jobs[0].id == "test_job"


# ═══════════════════════════════════════════════════════════════════
# 11. NEWS (providers/news/)
# ═══════════════════════════════════════════════════════════════════

class TestNewsProviders:
    """Test news RSS provider module."""

    def test_rss_provider_module_imports(self):
        from providers.news import rss_provider
        assert hasattr(rss_provider, "fetch_rss_entries")
        assert hasattr(rss_provider, "fetch_api_payload")

    def test_rss_provider_has_default_timeout(self):
        from providers.news.rss_provider import _DEFAULT_TIMEOUT
        assert isinstance(_DEFAULT_TIMEOUT, float)
        assert _DEFAULT_TIMEOUT > 0


# ═══════════════════════════════════════════════════════════════════
# 12. SECURITY (providers/security/)
# ═══════════════════════════════════════════════════════════════════

class TestSecurityProviders:
    """Test security encryption provider."""

    def test_encryption_module_imports(self):
        from providers.security import encryption
        assert hasattr(encryption, "Fernet")
        assert hasattr(encryption, "hashes")
        assert hasattr(encryption, "PBKDF2HMAC")

    def test_encryption_fernet_works(self):
        from providers.security.encryption import Fernet
        key = Fernet.generate_key()
        f = Fernet(key)
        token = f.encrypt(b"secret message")
        decrypted = f.decrypt(token)
        assert decrypted == b"secret message"

    def test_encryption_pbkdf2(self):
        from providers.security.encryption import PBKDF2HMAC, hashes
        from cryptography.hazmat.backends import default_backend
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"test-salt",
            iterations=100000,
            backend=default_backend(),
        )
        key = kdf.derive(b"password")
        assert len(key) == 32

    def test_threat_intel_module_imports(self):
        from providers.security import threat_intel
        assert hasattr(threat_intel, "fetch_tor_exit_list")

    def test_watchlist_module_imports(self):
        from providers.security import watchlist
        assert hasattr(watchlist, "screen_watchlist")
        assert hasattr(watchlist, "WatchlistProviderError")


# ═══════════════════════════════════════════════════════════════════
# 13. VOICE (providers/voice/)
# ═══════════════════════════════════════════════════════════════════

class TestVoiceProviders:
    """Test voice-to-text provider."""

    def test_voice_to_text_module_imports(self):
        from providers.voice import voice_to_text
        assert hasattr(voice_to_text, "transcribe_audio")
        assert hasattr(voice_to_text, "process_product_voice_command")
        assert hasattr(voice_to_text, "process_finance_voice_command")

    def test_process_product_voice_command(self):
        from providers.voice.voice_to_text import process_product_voice_command
        result = process_product_voice_command("add 5 red cotton shirts size M")
        assert result["color"] == "Red"
        assert result["size"] == "M"
        assert result["material"] == "Cotton"
        assert result["quantity"] == 5
        assert result["action"] == "add"

    def test_process_product_voice_command_remove(self):
        from providers.voice.voice_to_text import process_product_voice_command
        result = process_product_voice_command("remove 3 blue items")
        assert result["action"] == "remove"
        assert result["quantity"] == 3

    def test_process_product_voice_command_empty(self):
        from providers.voice.voice_to_text import process_product_voice_command
        result = process_product_voice_command("")
        assert result["quantity"] == 1
        assert result["action"] == "add"

    def test_process_finance_voice_command(self):
        from providers.voice.voice_to_text import process_finance_voice_command
        result = process_finance_voice_command("record expense $50 for office supplies")
        assert result["amount"] == 50.0
        assert result["task_type"] == "expense"
        assert result["category"] == "office supplies"

    def test_process_finance_voice_command_delete(self):
        from providers.voice.voice_to_text import process_finance_voice_command
        result = process_finance_voice_command("delete the payment")
        assert result["action"] == "delete"

    def test_process_finance_voice_command_empty(self):
        from providers.voice.voice_to_text import process_finance_voice_command
        result = process_finance_voice_command("")
        assert result["amount"] == 0.0
        assert result["action"] == "record"


# ═══════════════════════════════════════════════════════════════════
# 14. ANALYTICS (providers/analytics/)
# ═══════════════════════════════════════════════════════════════════

class TestAnalyticsProviders:
    """Test analytics provider."""

    def test_analytics_provider_exists(self):
        from providers.analytics.analytics import AnalyticsProvider
        assert AnalyticsProvider is not None

    def test_analytics_provider_instantiation(self):
        from providers.analytics.analytics import AnalyticsProvider
        provider = AnalyticsProvider()
        assert hasattr(provider, "get_dashboard_summary")
        assert hasattr(provider, "get_chatbot_analytics")
        assert hasattr(provider, "get_product_performance")
        assert hasattr(provider, "get_sales_trends")
        assert hasattr(provider, "get_ai_insights")

    def test_analytics_has_analytics_flag(self):
        from providers.analytics.analytics import HAS_ANALYTICS
        assert isinstance(HAS_ANALYTICS, bool)

    def test_analytics_provider_raises_without_key(self):
        from providers.analytics.analytics import AnalyticsProvider, HAS_ANALYTICS
        if HAS_ANALYTICS:
            pytest.skip("ANALYTICS_API_KEY is set, cannot test missing-key path")
        provider = AnalyticsProvider()
        result = provider.get_dashboard_summary()
        assert "message" in result


# ═══════════════════════════════════════════════════════════════════
# 15. QR (providers/qr/)
# ═══════════════════════════════════════════════════════════════════

class TestQRProviders:
    """Test QR parcel verification service."""

    def test_parcel_verification_service_imports(self):
        from providers.qr import parcel_verification_service
        assert hasattr(parcel_verification_service, "verify_parcel_photo")
        assert hasattr(parcel_verification_service, "verify_parcel_fast")

    def test_parcel_verification_service_functions_callable(self):
        from providers.qr.parcel_verification_service import verify_parcel_photo, verify_parcel_fast
        assert callable(verify_parcel_photo)
        assert callable(verify_parcel_fast)


# ═══════════════════════════════════════════════════════════════════
# 16. PROVIDER CONFIG
# ═══════════════════════════════════════════════════════════════════

class TestProviderConfig:
    """Test provider configuration."""

    def test_settings_exists(self):
        from providers.config import settings
        assert settings is not None

    def test_settings_has_required_fields(self):
        from providers.config import settings
        assert hasattr(settings, "ollama_base_url")
        assert hasattr(settings, "search_default_limit")
        assert hasattr(settings, "geo_default_country")
        assert hasattr(settings, "analytics_default_period_days")

    def test_settings_default_values(self):
        from providers.config import settings
        assert settings.search_default_limit > 0
        assert settings.analytics_default_period_days > 0
        assert isinstance(settings.bg_preset_models, dict)


# ═══════════════════════════════════════════════════════════════════
# 17. PROVIDER __init__ EXPORTS
# ═══════════════════════════════════════════════════════════════════

class TestProviderInit:
    """Test that provider package exports work."""

    def test_image_provider_exports(self):
        from providers.image import Image, ImageFilter, ImageEnhance, HAS_CV2
        assert Image is not None
        assert isinstance(HAS_CV2, bool)

    def test_image_provider_has_bg_remover_classes(self):
        from providers.image import CleanEdgeRefiner, SceneAnalyzer, HandRemover
        assert CleanEdgeRefiner is not None
        assert SceneAnalyzer is not None
        assert HandRemover is not None

    def test_image_provider_has_ocr_functions(self):
        from providers.image import parse_bill_text, parse_statement_csv
        assert callable(parse_bill_text)
        assert callable(parse_statement_csv)

    def test_image_provider_has_parcel_verification(self):
        from providers.image import verify_parcel_photo, verify_parcel_fast
        assert callable(verify_parcel_photo)
        assert callable(verify_parcel_fast)
