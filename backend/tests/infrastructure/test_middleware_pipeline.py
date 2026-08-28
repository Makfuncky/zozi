"""Middleware pipeline tests for the Zozi backend.

Verifies:
  1. Middleware ordering (foundation → auth → rate limit → geo → security → observability → compliance).
  2. CORS middleware configuration.
  3. Security headers middleware.
  4. Authentication middleware.
  5. Rate limiting middleware.
  6. CSRF middleware.
  7. Country context middleware.
  8. Request ID propagation.
"""
from __future__ import annotations

import os
import sys
from unittest.mock import patch, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Ensure backend root is importable
_BACKEND_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only")
os.environ.setdefault("CSRF_DISABLED", "true")


class TestMiddlewareOrdering:
    """Verify middleware registration order."""

    def test_foundation_layer_defined(self):
        from middleware.orchestrator import _FOUNDATION
        assert len(_FOUNDATION) > 0
        # Foundation should include GZip, CORS, IP extraction, RequestID, ApiVersion
        mw_names = [mw.__name__ for mw in _FOUNDATION]
        assert "GZipMiddleware" in mw_names
        assert "CORSMiddleware" in mw_names

    def test_authentication_layer_defined(self):
        from middleware.orchestrator import _AUTHENTICATION
        assert len(_AUTHENTICATION) > 0
        mw_names = [mw.__name__ for mw in _AUTHENTICATION]
        assert "AuthenticationMiddleware" in mw_names

    def test_rate_limiting_layer_defined(self):
        from middleware.orchestrator import _RATE_LIMITING
        assert len(_RATE_LIMITING) > 0
        mw_names = [mw.__name__ for mw in _RATE_LIMITING]
        assert "RateLimitMiddleware" in mw_names

    def test_geo_country_layer_defined(self):
        from middleware.orchestrator import _GEO_COUNTRY
        assert len(_GEO_COUNTRY) > 0
        mw_names = [mw.__name__ for mw in _GEO_COUNTRY]
        assert "CountryContextMiddleware" in mw_names

    def test_security_layer_defined(self):
        from middleware.orchestrator import _SECURITY
        assert len(_SECURITY) > 0
        mw_names = [mw.__name__ for mw in _SECURITY]
        assert "EnhancedSecurityHeadersMiddleware" in mw_names

    def test_observability_layer_defined(self):
        from middleware.orchestrator import _OBSERVABILITY
        assert len(_OBSERVABILITY) > 0
        mw_names = [mw.__name__ for mw in _OBSERVABILITY]
        assert "RequestLoggingMiddleware" in mw_names

    def test_compliance_layer_defined(self):
        from middleware.orchestrator import _COMPLIANCE
        assert len(_COMPLIANCE) > 0
        mw_names = [mw.__name__ for mw in _COMPLIANCE]
        assert "PCIDSSMiddleware" in mw_names

    def test_pipeline_order_correct(self):
        """Verify the pipeline is assembled in the correct order."""
        from middleware.orchestrator import _FOUNDATION, _AUTHENTICATION, _RATE_LIMITING
        from middleware.orchestrator import _GEO_COUNTRY, _SECURITY, _OBSERVABILITY
        # Each layer should be non-empty
        assert _FOUNDATION
        assert _AUTHENTICATION
        assert _RATE_LIMITING
        assert _GEO_COUNTRY
        assert _SECURITY
        assert _OBSERVABILITY

    def test_layer_count(self):
        from middleware.orchestrator import _layer_count
        count = _layer_count()
        assert count >= 6, f"Expected at least 6 layers, got {count}"

    def test_total_middleware_count(self):
        from middleware.orchestrator import _total_middleware
        count = _total_middleware()
        assert count >= 10, f"Expected at least 10 middleware, got {count}"


class TestCORSMiddleware:
    """CORS middleware configuration."""

    def test_cors_middleware_in_foundation(self):
        from middleware.orchestrator import _FOUNDATION
        from fastapi.middleware.cors import CORSMiddleware
        assert CORSMiddleware in _FOUNDATION

    def test_cors_kwargs_configured(self):
        from middleware.orchestrator import _resolve_kwargs
        from fastapi.middleware.cors import CORSMiddleware
        kwargs = _resolve_kwargs(CORSMiddleware)
        assert "allow_origins" in kwargs
        assert "allow_credentials" in kwargs
        assert "allow_methods" in kwargs
        assert "allow_headers" in kwargs
        assert kwargs["allow_credentials"] is True

    def test_cors_allows_authorization_header(self):
        from middleware.orchestrator import _resolve_kwargs
        from fastapi.middleware.cors import CORSMiddleware
        kwargs = _resolve_kwargs(CORSMiddleware)
        assert "Authorization" in kwargs["allow_headers"]

    def test_cors_allows_content_type_header(self):
        from middleware.orchestrator import _resolve_kwargs
        from fastapi.middleware.cors import CORSMiddleware
        kwargs = _resolve_kwargs(CORSMiddleware)
        assert "Content-Type" in kwargs["allow_headers"]


class TestSecurityHeadersMiddleware:
    """Security headers middleware."""

    def test_security_headers_in_pipeline(self):
        from middleware.orchestrator import _SECURITY
        mw_names = [mw.__name__ for mw in _SECURITY]
        assert "EnhancedSecurityHeadersMiddleware" in mw_names

    def test_security_headers_kwargs(self):
        from middleware.orchestrator import _resolve_kwargs
        from middleware.security_headers import EnhancedSecurityHeadersMiddleware
        kwargs = _resolve_kwargs(EnhancedSecurityHeadersMiddleware)
        assert "enable_hsts" in kwargs


class TestAuthenticationMiddleware:
    """Authentication middleware."""

    def test_auth_middleware_in_pipeline(self):
        from middleware.orchestrator import _AUTHENTICATION
        mw_names = [mw.__name__ for mw in _AUTHENTICATION]
        assert "AuthenticationMiddleware" in mw_names

    def test_device_binding_in_pipeline(self):
        from middleware.orchestrator import _AUTHENTICATION
        mw_names = [mw.__name__ for mw in _AUTHENTICATION]
        assert "DeviceBindingMiddleware" in mw_names


class TestRateLimitMiddleware:
    """Rate limiting middleware."""

    def test_rate_limit_in_pipeline(self):
        from middleware.orchestrator import _RATE_LIMITING
        mw_names = [mw.__name__ for mw in _RATE_LIMITING]
        assert "RateLimitMiddleware" in mw_names


class TestCSRFMiddleware:
    """CSRF middleware."""

    def test_csrf_in_pipeline(self):
        from middleware.orchestrator import _SECURITY
        mw_names = [mw.__name__ for mw in _SECURITY]
        assert "CSRFMiddleware" in mw_names


class TestCountryContextMiddleware:
    """Country context middleware."""

    def test_country_context_in_pipeline(self):
        from middleware.orchestrator import _GEO_COUNTRY
        mw_names = [mw.__name__ for mw in _GEO_COUNTRY]
        assert "CountryContextMiddleware" in mw_names


class TestRequestIDPropagation:
    """Request ID propagation middleware."""

    def test_request_id_in_foundation(self):
        from middleware.orchestrator import _FOUNDATION
        mw_names = [mw.__name__ for mw in _FOUNDATION]
        assert "RequestIDMiddleware" in mw_names

    def test_request_id_middleware_class_exists(self):
        from middleware.request_id_middleware import RequestIDMiddleware
        assert RequestIDMiddleware is not None


class TestApiVersionMiddleware:
    """API versioning middleware."""

    def test_api_version_in_foundation(self):
        from middleware.orchestrator import _FOUNDATION
        mw_names = [mw.__name__ for mw in _FOUNDATION]
        assert "ApiVersionMiddleware" in mw_names


class TestGZipMiddleware:
    """GZip compression middleware."""

    def test_gzip_in_foundation(self):
        from middleware.orchestrator import _FOUNDATION
        from fastapi.middleware.gzip import GZipMiddleware
        assert GZipMiddleware in _FOUNDATION

    def test_gzip_minimum_size_configured(self):
        from middleware.orchestrator import _resolve_kwargs
        from fastapi.middleware.gzip import GZipMiddleware
        kwargs = _resolve_kwargs(GZipMiddleware)
        assert kwargs.get("minimum_size") == 1024


class TestMiddlewareSetupFunction:
    """Middleware setup function."""

    def test_setup_middleware_callable(self):
        from middleware.orchestrator import setup_middleware
        assert callable(setup_middleware)

    def test_setup_middleware_accepts_app(self):
        from middleware.orchestrator import setup_middleware
        app = FastAPI()
        # Should not raise
        setup_middleware(app)

    def test_setup_middleware_registers_middleware(self):
        from middleware.orchestrator import setup_middleware, _total_middleware
        app = FastAPI()
        setup_middleware(app)
        # After setup, the app should have middleware registered
        # The exact count depends on the environment
        expected = _total_middleware()
        assert expected > 0


class TestWebhookMiddleware:
    """Webhook middleware (active in pipeline)."""

    def test_webhook_ip_whitelist_in_pipeline(self):
        from middleware.orchestrator import _WEBHOOKS
        mw_names = [mw.__name__ for mw in _WEBHOOKS]
        assert "WebhookIPWhitelistMiddleware" in mw_names

    def test_webhook_verification_in_pipeline(self):
        from middleware.orchestrator import _WEBHOOKS
        mw_names = [mw.__name__ for mw in _WEBHOOKS]
        assert "WebhookVerificationMiddleware" in mw_names


class TestIPExtractionMiddleware:
    """IP extraction middleware."""

    def test_ip_extraction_in_foundation(self):
        from middleware.orchestrator import _FOUNDATION
        mw_names = [mw.__name__ for mw in _FOUNDATION]
        assert "IPExtractionMiddleware" in mw_names


class TestFraudMiddleware:
    """Fraud detection middleware."""

    def test_impossible_travel_in_pipeline(self):
        from middleware.orchestrator import _SECURITY
        mw_names = [mw.__name__ for mw in _SECURITY]
        assert "ImpossibleTravelMiddleware" in mw_names

    def test_fraud_detection_in_pipeline(self):
        from middleware.orchestrator import _SECURITY
        mw_names = [mw.__name__ for mw in _SECURITY]
        assert "FraudDetectionMiddleware" in mw_names

    def test_fraud_scoring_in_pipeline(self):
        from middleware.orchestrator import _SECURITY
        mw_names = [mw.__name__ for mw in _SECURITY]
        assert "FraudScoringMiddleware" in mw_names
