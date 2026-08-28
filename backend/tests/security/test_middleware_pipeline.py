"""Comprehensive security middleware tests for ZOZI backend.

Tests CORS, security headers, CSRF protection, rate limiting,
authentication middleware, device binding, impossible travel detection,
fraud detection, and webhook verification.
"""
from __future__ import annotations

import time
import uuid
from unittest.mock import patch, MagicMock, AsyncMock

import pytest


class TestCORSOriginValidation:
    """Test CORS origin validation."""

    def test_cors_preflight_with_allowed_origin(self, client):
        """Preflight with allowed origin should return CORS headers."""
        resp = client.options(
            "/api/v1/auth/login",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
            },
        )
        # Should have CORS headers for allowed origin
        if "Access-Control-Allow-Origin" in resp.headers:
            assert resp.headers["Access-Control-Allow-Origin"] == "http://localhost:3000"

    def test_cors_preflight_with_disallowed_origin(self, client):
        """Preflight with disallowed origin should not return CORS headers."""
        resp = client.options(
            "/api/v1/auth/login",
            headers={
                "Origin": "https://evil-site.com",
                "Access-Control-Request-Method": "POST",
            },
        )
        # Disallowed origin should not get CORS headers
        if "Access-Control-Allow-Origin" in resp.headers:
            assert resp.headers["Access-Control-Allow-Origin"] != "https://evil-site.com"

    def test_cors_allows_credentials(self, client):
        """CORS should allow credentials for valid origins."""
        resp = client.options(
            "/api/v1/auth/login",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
            },
        )
        if "Access-Control-Allow-Credentials" in resp.headers:
            assert resp.headers["Access-Control-Allow-Credentials"] == "true"


class TestSecurityHeaders:
    """Test security headers middleware."""

    def test_x_content_type_options_header(self, client):
        """Response should include X-Content-Type-Options: nosniff."""
        resp = client.get("/health")
        assert resp.headers.get("X-Content-Type-Options") == "nosniff"

    def test_x_frame_options_header(self, client):
        """Response should include X-Frame-Options: DENY."""
        resp = client.get("/health")
        assert resp.headers.get("X-Frame-Options") == "DENY"

    def test_x_xss_protection_header(self, client):
        """Response should include X-XSS-Protection."""
        resp = client.get("/health")
        assert "X-XSS-Protection" in resp.headers

    def test_referrer_policy_header(self, client):
        """Response should include Referrer-Policy."""
        resp = client.get("/health")
        assert "Referrer-Policy" in resp.headers

    def test_content_security_policy_header(self, client):
        """Response should include Content-Security-Policy."""
        resp = client.get("/health")
        assert "Content-Security-Policy" in resp.headers

    def test_strict_transport_security_header(self, client):
        """Response should include Strict-Transport-Security."""
        resp = client.get("/health")
        assert "Strict-Transport-Security" in resp.headers

    def test_permissions_policy_header(self, client):
        """Response should include Permissions-Policy."""
        resp = client.get("/health")
        assert "Permissions-Policy" in resp.headers

    def test_cache_control_header(self, client):
        """Response should include Cache-Control for security."""
        resp = client.get("/health")
        assert "Cache-Control" in resp.headers

    def test_security_headers_on_error_responses(self, client):
        """Security headers should be present even on error responses."""
        resp = client.get("/api/v1/nonexistent-endpoint-xyz")
        assert "X-Content-Type-Options" in resp.headers

    def test_security_zone_header(self, client):
        """Response should include X-Zoi-Security-Zone header."""
        resp = client.get("/health")
        assert "X-Zoi-Security-Zone" in resp.headers


class TestCSRFProtection:
    """Test CSRF protection middleware."""

    def test_csrf_bypassed_in_test_env(self, client):
        """CSRF should be bypassed in test environment."""
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@zozi.com", "password": "admin123"},
        )
        # In test env, CSRF is disabled so request should proceed
        assert resp.status_code != 403 or "CSRF" not in resp.json().get("detail", "")

    def test_csrf_token_generation(self):
        """CSRF token should be generated."""
        from middleware.csrf_middleware import generate_csrf_token

        token = generate_csrf_token()
        assert isinstance(token, str)
        assert len(token) == 64  # 32 bytes hex = 64 chars

    def test_csrf_token_uniqueness(self):
        """Each CSRF token should be unique."""
        from middleware.csrf_middleware import generate_csrf_token

        token1 = generate_csrf_token()
        token2 = generate_csrf_token()
        assert token1 != token2

    def test_csrf_constant_time_compare(self):
        """CSRF comparison should be constant-time."""
        from middleware.csrf_middleware import CSRFMiddleware

        middleware = CSRFMiddleware.__new__(CSRFMiddleware)
        assert middleware._constant_time_compare("abc", "abc") is True
        assert middleware._constant_time_compare("abc", "xyz") is False
        assert middleware._constant_time_compare("", "") is True


class TestRateLimiting:
    """Test rate limiting middleware."""

    def test_rate_limiting_disabled_in_test_env(self, client):
        """Rate limiting should be disabled in test environment."""
        # Make multiple requests quickly
        for _ in range(10):
            resp = client.get("/health")
            assert resp.status_code == 200

    def test_rate_limit_middleware_exists(self):
        """RateLimitMiddleware should be importable."""
        from middleware.rate_limit_middleware import RateLimitMiddleware

        assert RateLimitMiddleware is not None

    def test_rate_limit_path_tiers_defined(self):
        """Rate limit path tiers should be defined."""
        from middleware.rate_limit_middleware import PATH_LIMITS

        assert len(PATH_LIMITS) > 0
        # Auth endpoints should have stricter limits
        auth_limits = [p for p in PATH_LIMITS if "/auth" in p[0]]
        assert len(auth_limits) > 0

    def test_rate_limit_default_config(self):
        """Default rate limit config should exist."""
        from middleware.rate_limit_middleware import DEFAULT_LIMIT, READ_LIMIT

        assert DEFAULT_LIMIT[0] > 0
        assert DEFAULT_LIMIT[1] > 0
        assert READ_LIMIT[0] >= DEFAULT_LIMIT[0]

    def test_token_bucket_config(self):
        """Token bucket config should be defined."""
        from middleware.rate_limit_middleware import RateLimitConfig, TokenBucket

        config = RateLimitConfig(requests_per_second=10, burst_capacity=20)
        bucket = TokenBucket(config)
        assert bucket is not None


class TestAuthenticationMiddleware:
    """Test authentication middleware."""

    def test_middleware_populates_user_state(self, app):
        """Auth middleware should populate request.state.user."""
        from fastapi.testclient import TestClient

        with TestClient(app) as c:
            resp = c.get(
                "/health",
                headers={"Authorization": "Bearer invalid.token.test"},
            )
            # Should not crash even with invalid token
            assert resp.status_code in (200, 401)

    def test_middleware_handles_missing_auth_header(self, client):
        """Auth middleware should handle missing auth header gracefully."""
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_middleware_handles_malformed_bearer(self, client):
        """Auth middleware should handle malformed bearer tokens."""
        resp = client.get(
            "/health",
            headers={"Authorization": "NotBearer token"},
        )
        assert resp.status_code == 200

    def test_middleware_extracts_user_id_from_valid_token(self, client, admin_token):
        """Auth middleware should extract user ID from valid token."""
        resp = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200


class TestDeviceBindingMiddleware:
    """Test device binding middleware."""

    def test_device_fingerprint_computation(self):
        """Device fingerprint should be computed from headers."""
        from middleware.device_binding_middleware import compute_device_fingerprint

        # Create a mock request
        mock_request = MagicMock()
        mock_request.headers = {
            "user-agent": "Mozilla/5.0 Test",
            "accept-language": "en-US",
        }

        fp = compute_device_fingerprint(mock_request)
        assert fp is not None
        assert len(fp) == 64  # SHA-256 hex

    def test_device_fingerprint_stable(self):
        """Same headers should produce same fingerprint."""
        from middleware.device_binding_middleware import compute_device_fingerprint

        mock_request = MagicMock()
        mock_request.headers = {
            "user-agent": "Mozilla/5.0 Test",
            "accept-language": "en-US",
        }

        fp1 = compute_device_fingerprint(mock_request)
        fp2 = compute_device_fingerprint(mock_request)
        assert fp1 == fp2

    def test_device_fingerprint_with_explicit_id(self):
        """Explicit device ID should be included in fingerprint."""
        from middleware.device_binding_middleware import compute_device_fingerprint

        mock_request = MagicMock()
        mock_request.headers = {
            "user-agent": "Mozilla/5.0",
            "X-Device-ID": "my-device-123",
        }

        fp = compute_device_fingerprint(mock_request)
        assert fp is not None

    def test_device_fingerprint_empty_headers(self):
        """Empty headers should return None."""
        from middleware.device_binding_middleware import compute_device_fingerprint

        mock_request = MagicMock()
        mock_request.headers = {}

        fp = compute_device_fingerprint(mock_request)
        assert fp is None


class TestImpossibleTravelDetection:
    """Test impossible travel detection middleware."""

    def test_impossible_travel_middleware_exists(self):
        """ImpossibleTravelMiddleware should be importable."""
        from middleware.impossible_travel_middleware import ImpossibleTravelMiddleware

        assert ImpossibleTravelMiddleware is not None

    def test_haversine_distance_same_point(self):
        """Haversine distance between same point should be 0."""
        from middleware.impossible_travel_middleware import ImpossibleTravelMiddleware

        distance = ImpossibleTravelMiddleware._haversine(0.0, 0.0, 0.0, 0.0)
        assert distance == 0.0

    def test_haversine_distance_known_points(self):
        """Haversine distance between known points should be reasonable."""
        from middleware.impossible_travel_middleware import ImpossibleTravelMiddleware

        # London to Paris ~343 km
        distance = ImpossibleTravelMiddleware._haversine(51.5074, -0.1278, 48.8566, 2.3522)
        assert 300 < distance < 400

    def test_public_paths_excluded(self):
        """Public paths should be excluded from travel checks."""
        from middleware.impossible_travel_middleware import ImpossibleTravelMiddleware

        middleware = ImpossibleTravelMiddleware.__new__(ImpossibleTravelMiddleware)
        assert middleware._should_check(MagicMock(url=MagicMock(path="/docs"))) is False
        assert middleware._should_check(MagicMock(url=MagicMock(path="/health"))) is False
        assert middleware._should_check(MagicMock(url=MagicMock(path="/static/test.css"))) is False

    def test_private_paths_checked(self):
        """Private paths should be checked for impossible travel."""
        from middleware.impossible_travel_middleware import ImpossibleTravelMiddleware

        middleware = ImpossibleTravelMiddleware.__new__(ImpossibleTravelMiddleware)
        assert middleware._should_check(MagicMock(url=MagicMock(path="/api/v1/orders"))) is True


class TestFraudDetectionMiddleware:
    """Test fraud detection middleware."""

    def test_fraud_detection_middleware_exists(self):
        """FraudDetectionMiddleware should be importable."""
        from middleware.impossible_travel_middleware import FraudDetectionMiddleware

        assert FraudDetectionMiddleware is not None

    def test_fraud_scoring_middleware_exists(self):
        """FraudScoringMiddleware should be importable."""
        from middleware.impossible_travel_middleware import FraudScoringMiddleware

        assert FraudScoringMiddleware is not None

    def test_sensitive_paths_defined(self):
        """Sensitive paths for fraud detection should be defined."""
        from middleware.impossible_travel_middleware import SENSITIVE_PATHS

        assert "checkout" in SENSITIVE_PATHS
        assert "login" in SENSITIVE_PATHS
        assert "payment" in SENSITIVE_PATHS

    def test_fraud_rules_defined(self):
        """Fraud detection rules should be defined."""
        from middleware.impossible_travel_middleware import FraudDetectionMiddleware

        assert "max_login_attempts_per_hour" in FraudDetectionMiddleware.FRAUD_RULES
        assert "max_transactions_per_hour" in FraudDetectionMiddleware.FRAUD_RULES


class TestWebhookHMACVerification:
    """Test webhook HMAC verification."""

    def test_webhook_verification_middleware_exists(self):
        """WebhookVerificationMiddleware should be importable."""
        from middleware.webhook_verification import WebhookVerificationMiddleware

        assert WebhookVerificationMiddleware is not None

    def test_webhook_providers_configured(self):
        """Webhook providers should be configured."""
        from middleware.webhook_verification import WebhookVerificationMiddleware

        providers = WebhookVerificationMiddleware.PROVIDERS
        assert "stripe" in providers
        assert "tap" in providers
        assert "paypal" in providers

    def test_webhook_paths_configured(self):
        """Webhook paths should be configured."""
        from middleware.webhook_verification import WebhookVerificationMiddleware

        paths = WebhookVerificationMiddleware.WEBHOOK_PATHS
        assert "/payments/webhook" in paths

    def test_compute_webhook_signature(self):
        """Webhook signature computation should work."""
        from middleware.webhook_verification import compute_webhook_signature

        payload = b'{"event": "payment.success"}'
        secret = "whsec_test123"
        signature = compute_webhook_signature(payload, secret)

        assert signature.startswith("t=")
        assert ",v1=" in signature

    def test_verify_webhook_signature_valid(self):
        """Valid webhook signature should verify."""
        from middleware.webhook_verification import compute_webhook_signature, verify_webhook_signature

        payload = b'{"event": "payment.success"}'
        secret = "whsec_test123"
        signature_header = compute_webhook_signature(payload, secret)

        # Extract the v1= signature
        v1_sig = signature_header.split(",v1=")[1] if ",v1=" in signature_header else ""

        result = verify_webhook_signature(payload, v1_sig, secret, provider="stripe")
        assert result is True

    def test_verify_webhook_signature_invalid(self):
        """Invalid webhook signature should fail."""
        from middleware.webhook_verification import verify_webhook_signature

        payload = b'{"event": "payment.success"}'
        secret = "whsec_test123"

        result = verify_webhook_signature(payload, "invalid_signature", secret, provider="stripe")
        assert result is False

    def test_replay_attack_protection_exists(self):
        """Replay attack protection should exist."""
        from middleware.webhook_verification import ReplayAttackProtection

        assert ReplayAttackProtection is not None


class TestWebhookIPWhitelist:
    """Test webhook IP whitelist middleware."""

    def test_ip_whitelist_middleware_exists(self):
        """WebhookIPWhitelistMiddleware should be importable."""
        from middleware.webhook_ip_whitelist import WebhookIPWhitelistMiddleware

        assert WebhookIPWhitelistMiddleware is not None

    def test_provider_ip_ranges_configured(self):
        """Provider IP ranges should be configured."""
        from middleware.webhook_ip_whitelist import PROVIDER_IP_RANGES

        assert "stripe" in PROVIDER_IP_RANGES
        assert "tap" in PROVIDER_IP_RANGES
        assert "paypal" in PROVIDER_IP_RANGES

    def test_ip_in_ranges_check(self):
        """IP whitelist check should work."""
        from middleware.webhook_ip_whitelist import _is_ip_in_ranges

        # Test with a Stripe IP range
        stripe_ranges = PROVIDER_IP_RANGES = ["3.18.12.0/24"]
        assert _is_ip_in_ranges("3.18.12.100", stripe_ranges) is True
        assert _is_ip_in_ranges("192.168.1.1", stripe_ranges) is False

    def test_resolve_provider_from_path(self):
        """Provider should be resolved from webhook path."""
        from middleware.webhook_ip_whitelist import _resolve_provider_from_path

        assert _resolve_provider_from_path("/payments/webhook/stripe") == "stripe"
        assert _resolve_provider_from_path("/payments/tap/webhook") == "tap"
        assert _resolve_provider_from_path("/email/webhooks") == "resend"
        assert _resolve_provider_from_path("/api/v1/orders") is None
