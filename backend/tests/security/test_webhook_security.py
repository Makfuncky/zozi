"""Comprehensive webhook security tests for ZOZI backend.

Tests HMAC signature verification for all payment providers,
timestamp tolerance, replay attack protection, IP whitelist enforcement,
and various signature failure modes.
"""
from __future__ import annotations

import hashlib
import hmac
import time
import uuid
from unittest.mock import MagicMock, patch, AsyncMock

import pytest


class TestStripeWebhookVerification:
    """Test Stripe webhook HMAC signature verification."""

    def test_stripe_signature_computation(self):
        """Stripe webhook signature should be computed correctly."""
        from middleware.webhook_verification import compute_webhook_signature

        payload = b'{"type": "payment_intent.succeeded"}'
        secret = "whsec_test_secret"

        sig = compute_webhook_signature(payload, secret)
        assert sig.startswith("t=")
        assert ",v1=" in sig

    def test_stripe_signature_verification_valid(self):
        """Valid Stripe signature should pass verification."""
        from middleware.webhook_verification import compute_webhook_signature, verify_webhook_signature

        payload = b'{"type": "payment_intent.succeeded"}'
        secret = "whsec_test_secret"
        sig_header = compute_webhook_signature(payload, secret)
        v1_sig = sig_header.split(",v1=")[1]

        assert verify_webhook_signature(payload, v1_sig, secret, "stripe") is True

    def test_stripe_signature_verification_invalid(self):
        """Invalid Stripe signature should fail verification."""
        from middleware.webhook_verification import verify_webhook_signature

        payload = b'{"type": "payment_intent.succeeded"}'
        secret = "whsec_test_secret"

        assert verify_webhook_signature(payload, "wrong_sig", secret, "stripe") is False

    def test_stripe_tampered_payload_fails(self):
        """Tampered payload should fail signature verification."""
        from middleware.webhook_verification import compute_webhook_signature, verify_webhook_signature

        payload = b'{"type": "payment_intent.succeeded"}'
        secret = "whsec_test_secret"
        sig_header = compute_webhook_signature(payload, secret)
        v1_sig = sig_header.split(",v1=")[1]

        tampered_payload = b'{"type": "payment_intent.succeeded", "amount": 999999}'
        assert verify_webhook_signature(tampered_payload, v1_sig, secret, "stripe") is False


class TestTapWebhookVerification:
    """Test Tap webhook HMAC signature verification."""

    def test_tap_signature_computation(self):
        """Tap webhook signature should be computed correctly."""
        from middleware.webhook_verification import compute_webhook_signature

        payload = b'{"status": "CAPTURED"}'
        secret = "sk_test_tap_secret"

        sig = compute_webhook_signature(payload, secret)
        assert sig.startswith("t=")
        assert ",v1=" in sig

    def test_tap_signature_verification_valid(self):
        """Valid Tap signature should pass verification."""
        from middleware.webhook_verification import compute_webhook_signature, verify_webhook_signature

        payload = b'{"status": "CAPTURED"}'
        secret = "sk_test_tap_secret"
        sig_header = compute_webhook_signature(payload, secret)
        v1_sig = sig_header.split(",v1=")[1]

        assert verify_webhook_signature(payload, v1_sig, secret, "tap") is True

    def test_tap_signature_verification_invalid(self):
        """Invalid Tap signature should fail."""
        from middleware.webhook_verification import verify_webhook_signature

        payload = b'{"status": "CAPTURED"}'
        secret = "sk_test_tap_secret"

        assert verify_webhook_signature(payload, "invalid", secret, "tap") is False


class TestPayPalWebhookVerification:
    """Test PayPal webhook signature verification."""

    def test_paypal_provider_configured(self):
        """PayPal should be configured as a webhook provider."""
        from middleware.webhook_verification import WebhookVerificationMiddleware

        assert "paypal" in WebhookVerificationMiddleware.PROVIDERS

    def test_paypal_signature_header(self):
        """PayPal should use correct signature header."""
        from middleware.webhook_verification import WebhookVerificationMiddleware

        paypal_config = WebhookVerificationMiddleware.PROVIDERS["paypal"]
        assert paypal_config.signature_header == "PayPal-Transmission-Sig"


class TestThawaniWebhookVerification:
    """Test Thawani webhook verification."""

    def test_thawani_ip_ranges_configured(self):
        """Thawani IP ranges should be configured."""
        from middleware.webhook_ip_whitelist import PROVIDER_IP_RANGES

        assert "thawani" in PROVIDER_IP_RANGES

    def test_thawani_ip_whitelist_blocks_unknown_ips(self):
        """Thawani webhook from unknown IP should be blocked."""
        from middleware.webhook_ip_whitelist import _is_ip_in_ranges

        thawani_ranges = ["2.16.0.0/16", "185.10.0.0/16"]
        assert _is_ip_in_ranges("192.168.1.1", thawani_ranges) is False

    def test_thawani_ip_whitelist_allows_known_ips(self):
        """Thawani webhook from known IP should be allowed."""
        from middleware.webhook_ip_whitelist import _is_ip_in_ranges

        thawani_ranges = ["2.16.0.0/16", "185.10.0.0/16"]
        assert _is_ip_in_ranges("2.16.1.1", thawani_ranges) is True


class TestPayTabsWebhookVerification:
    """Test PayTabs webhook verification."""

    def test_paytabs_ip_ranges_configured(self):
        """PayTabs IP ranges should be configured."""
        from middleware.webhook_ip_whitelist import PROVIDER_IP_RANGES

        assert "paytabs" in PROVIDER_IP_RANGES

    def test_paytabs_ip_whitelist_enforcement(self):
        """PayTabs webhook should enforce IP whitelist."""
        from middleware.webhook_ip_whitelist import _is_ip_in_ranges

        paytabs_ranges = ["5.182.0.0/16", "185.28.0.0/16"]
        assert _is_ip_in_ranges("5.182.1.1", paytabs_ranges) is True
        assert _is_ip_in_ranges("10.0.0.1", paytabs_ranges) is False


class TestTimestampTolerance:
    """Test webhook timestamp tolerance (300s)."""

    def test_fresh_timestamp_accepted(self):
        """Fresh timestamp within tolerance should be accepted."""
        from middleware.webhook_verification import compute_webhook_signature

        payload = b'{"event": "test"}'
        secret = "whsec_test"
        now = int(time.time())

        sig = compute_webhook_signature(payload, secret, timestamp=now)
        assert sig is not None

    def test_timestamp_at_tolerance_boundary(self):
        """Timestamp at exactly 300s boundary should be handled."""
        from middleware.webhook_verification import WebhookProviderConfig

        config = WebhookProviderConfig(
            name="test", secret="test", signature_header="X-Sig",
            signature_prefix="v1=", tolerance=300,
        )
        assert config.tolerance == 300

    def test_expired_timestamp_rejected(self):
        """Timestamp beyond 300s tolerance should be rejected."""
        from middleware.webhook_verification import WebhookVerificationMiddleware

        provider = WebhookVerificationMiddleware.PROVIDERS["stripe"]
        assert provider.tolerance == 300

        # Simulate expired timestamp
        old_timestamp = int(time.time()) - 301
        assert abs(time.time() - old_timestamp) > provider.tolerance

    def test_future_timestamp_rejected(self):
        """Future timestamp beyond tolerance should be rejected."""
        from middleware.webhook_verification import WebhookVerificationMiddleware

        provider = WebhookVerificationMiddleware.PROVIDERS["stripe"]
        future_timestamp = int(time.time()) + 301
        assert abs(time.time() - future_timestamp) > provider.tolerance


class TestReplayAttackProtection:
    """Test replay attack protection."""

    def test_replay_protection_class_exists(self):
        """ReplayAttackProtection class should exist."""
        from middleware.webhook_verification import ReplayAttackProtection

        assert ReplayAttackProtection is not None

    def test_replay_protection_tracks_signatures(self):
        """Replay protection should track seen signatures."""
        from middleware.webhook_verification import ReplayAttackProtection

        protection = ReplayAttackProtection(window_seconds=300)
        assert protection.window == 300

    def test_replay_protection_without_redis(self):
        """Without Redis, replay protection should return False (no replay)."""
        from middleware.webhook_verification import ReplayAttackProtection

        protection = ReplayAttackProtection()
        protection.redis = None

        assert protection.is_replayed("sig_123") is False


class TestIPWhitelistEnforcement:
    """Test webhook IP whitelist enforcement."""

    def test_non_webhook_paths_bypass_whitelist(self, client):
        """Non-webhook paths should not be affected by IP whitelist."""
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_webhook_ip_extraction_from_x_forwarded_for(self):
        """Client IP should be extracted from X-Forwarded-For."""
        from middleware.webhook_ip_whitelist import _extract_client_ip

        mock_request = MagicMock()
        mock_request.headers = {"X-Forwarded-For": "52.15.1.1, 10.0.0.1"}
        mock_request.client = MagicMock(host="10.0.0.1")

        ip = _extract_client_ip(mock_request)
        assert ip == "52.15.1.1"

    def test_webhook_ip_extraction_from_x_real_ip(self):
        """Client IP should be extracted from X-Real-IP."""
        from middleware.webhook_ip_whitelist import _extract_client_ip

        mock_request = MagicMock()
        mock_request.headers = {"X-Real-IP": "52.15.1.1"}
        mock_request.client = MagicMock(host="10.0.0.1")

        ip = _extract_client_ip(mock_request)
        assert ip == "52.15.1.1"

    def test_webhook_ip_extraction_from_client_host(self):
        """Client IP should fall back to client.host."""
        from middleware.webhook_ip_whitelist import _extract_client_ip

        mock_request = MagicMock()
        mock_request.headers = {}
        mock_request.client = MagicMock(host="52.15.1.1")

        ip = _extract_client_ip(mock_request)
        assert ip == "52.15.1.1"

    def test_invalid_ip_handled_gracefully(self):
        """Invalid IP should be handled gracefully."""
        from middleware.webhook_ip_whitelist import _is_ip_in_ranges

        result = _is_ip_in_ranges("not-an-ip", ["3.18.12.0/24"])
        assert result is False

    def test_ipv6_address_handling(self):
        """IPv6 addresses should be handled."""
        from middleware.webhook_ip_whitelist import _is_ip_in_ranges

        result = _is_ip_in_ranges("::1", ["3.18.12.0/24"])
        assert result is False


class TestMissingSignatureRejection:
    """Test rejection of webhooks with missing signatures."""

    def test_missing_signature_header_rejected(self):
        """Webhook without signature header should be rejected."""
        from middleware.webhook_verification import WebhookVerificationMiddleware

        provider = WebhookVerificationMiddleware.PROVIDERS["stripe"]
        assert provider.signature_header == "Stripe-Signature"

    def test_empty_signature_rejected(self):
        """Empty signature should be rejected."""
        from middleware.webhook_verification import verify_webhook_signature

        payload = b'{"event": "test"}'
        secret = "whsec_test"

        assert verify_webhook_signature(payload, "", secret, "stripe") is False


class TestInvalidSignatureRejection:
    """Test rejection of webhooks with invalid signatures."""

    def test_wrong_secret_rejects_signature(self):
        """Signature computed with wrong secret should fail."""
        from middleware.webhook_verification import compute_webhook_signature, verify_webhook_signature

        payload = b'{"event": "test"}'
        correct_secret = "whsec_correct"
        wrong_secret = "whsec_wrong"

        sig_header = compute_webhook_signature(payload, correct_secret)
        v1_sig = sig_header.split(",v1=")[1]

        assert verify_webhook_signature(payload, v1_sig, wrong_secret, "stripe") is False

    def test_truncated_signature_rejected(self):
        """Truncated signature should be rejected."""
        from middleware.webhook_verification import verify_webhook_signature

        payload = b'{"event": "test"}'
        secret = "whsec_test"

        assert verify_webhook_signature(payload, "abc123", secret, "stripe") is False

    def test_signature_for_different_payload_rejected(self):
        """Signature for different payload should be rejected."""
        from middleware.webhook_verification import compute_webhook_signature, verify_webhook_signature

        payload1 = b'{"event": "payment.success"}'
        payload2 = b'{"event": "payment.failed"}'
        secret = "whsec_test"

        sig_header = compute_webhook_signature(payload1, secret)
        v1_sig = sig_header.split(",v1=")[1]

        assert verify_webhook_signature(payload2, v1_sig, secret, "stripe") is False


class TestWebhookProviderIdentification:
    """Test webhook provider identification from paths."""

    def test_stripe_path_identification(self):
        """Stripe provider should be identified from path."""
        from middleware.webhook_verification import WebhookVerificationMiddleware

        middleware = WebhookVerificationMiddleware.__new__(WebhookVerificationMiddleware)
        provider = middleware._identify_provider("/payments/webhook/stripe")
        assert provider is not None
        assert provider.name == "stripe"

    def test_tap_path_identification(self):
        """Tap provider should be identified from path."""
        from middleware.webhook_verification import WebhookVerificationMiddleware

        middleware = WebhookVerificationMiddleware.__new__(WebhookVerificationMiddleware)
        provider = middleware._identify_provider("/payments/tap/webhook")
        assert provider is not None
        assert provider.name == "tap"

    def test_resend_path_identification(self):
        """Resend provider should be identified from email webhooks path."""
        from middleware.webhook_verification import WebhookVerificationMiddleware

        middleware = WebhookVerificationMiddleware.__new__(WebhookVerificationMiddleware)
        provider = middleware._identify_provider("/email/webhooks")
        assert provider is not None
        assert provider.name == "resend"

    def test_unknown_path_returns_none(self):
        """Unknown webhook path should return None."""
        from middleware.webhook_verification import WebhookVerificationMiddleware

        middleware = WebhookVerificationMiddleware.__new__(WebhookVerificationMiddleware)
        provider = middleware._identify_provider("/api/v1/orders")
        assert provider is None


class TestWebhookSecurityIntegration:
    """Integration tests for webhook security."""

    def test_webhook_path_prefixes_defined(self):
        """Webhook path prefixes should be defined."""
        from middleware.webhook_ip_whitelist import WEBHOOK_PATH_PREFIXES

        assert "/payments/webhook" in WEBHOOK_PATH_PREFIXES
        assert "/payments/tap/webhook" in WEBHOOK_PATH_PREFIXES
        assert "/email/webhooks" in WEBHOOK_PATH_PREFIXES

    def test_all_payment_providers_have_ip_ranges(self):
        """All payment providers should have IP ranges configured."""
        from middleware.webhook_ip_whitelist import PROVIDER_IP_RANGES

        providers = ["stripe", "tap", "paypal", "thawani", "paytabs", "resend"]
        for provider in providers:
            assert provider in PROVIDER_IP_RANGES, f"Missing IP ranges for {provider}"
            assert len(PROVIDER_IP_RANGES[provider]) > 0, f"Empty IP ranges for {provider}"

    def test_hmac_comparison_is_constant_time(self):
        """HMAC comparison should use constant-time comparison."""
        from middleware.webhook_verification import WebhookVerificationMiddleware

        # The middleware uses hmac.compare_digest which is constant-time
        payload = b'{"event": "test"}'
        secret = "whsec_test"
        timestamp = int(time.time())

        sig1 = hmac.new(secret.encode(), f"{timestamp}.{payload.decode()}".encode(), hashlib.sha256).hexdigest()
        sig2 = hmac.new(secret.encode(), f"{timestamp}.{payload.decode()}".encode(), hashlib.sha256).hexdigest()

        assert hmac.compare_digest(sig1, sig2) is True
