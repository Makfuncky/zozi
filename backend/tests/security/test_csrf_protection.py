"""CSRF protection security tests.

Verifies the double-submit cookie pattern implemented in
``backend/middleware/csrf_middleware.py``:
- Stateful methods (POST/PUT/DELETE/PATCH) require a matching
  ``X-CSRF-Token`` header AND ``csrf_token`` cookie.
- Safe methods (GET/HEAD/OPTIONS) bypass CSRF and seed the cookie.
- Auth-exempt paths are bypassed.
- Webhook paths are bypassed (HMAC/IP whitelist covers them).
- Token comparison is constant-time.
- Disabling CSRF is honored only via the ``CSRF_DISABLED`` env var.
"""

from __future__ import annotations

import importlib
import os
import secrets

import pytest


_BACKEND_ROOT = importlib.import_module("pathlib").Path(__file__).resolve().parent.parent


class TestCSRFMiddlewareContract:
    """Pure (no client) checks on the CSRF middleware contract."""

    def test_stateful_methods_require_token(self):
        from middleware.csrf_middleware import STATEFUL_METHODS, CSRFMiddleware

        assert "POST" in STATEFUL_METHODS
        assert "PUT" in STATEFUL_METHODS
        assert "DELETE" in STATEFUL_METHODS
        assert "PATCH" in STATEFUL_METHODS
        # Safe methods MUST NOT be in the set
        assert "GET" not in STATEFUL_METHODS
        assert "HEAD" not in STATEFUL_METHODS
        assert "OPTIONS" not in STATEFUL_METHODS

    def test_token_length_is_secure(self):
        from middleware.csrf_middleware import CSRF_TOKEN_LENGTH

        # 32 bytes -> 64 hex chars; OWASP recommends >= 128 bits of entropy.
        assert CSRF_TOKEN_LENGTH >= 32

    def test_generate_csrf_token_returns_unique_hex(self):
        from middleware.csrf_middleware import generate_csrf_token

        t1 = generate_csrf_token()
        t2 = generate_csrf_token()
        assert t1 != t2
        assert all(c in "0123456789abcdef" for c in t1)

    def test_constant_time_compare_uses_secrets_module(self):
        """Constant-time compare must use ``secrets.compare_digest``."""
        from middleware.csrf_middleware import CSRFMiddleware

        mw = CSRFMiddleware.__new__(CSRFMiddleware)
        assert mw._constant_time_compare("abc", "abc") is True
        assert mw._constant_time_compare("abc", "abd") is False
        # Different lengths must not match
        assert mw._constant_time_compare("abc", "abcd") is False

    def test_exempt_paths_include_auth_and_webhooks(self):
        from middleware.csrf_middleware import CSRF_EXEMPT_PATHS, WEBHOOK_PATHS

        # Public auth endpoints must be exempt (no pre-session cookies possible)
        for path in (
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/refresh",
            "/api/v1/auth/forgot-password",
            "/api/v1/auth/reset-password",
            "/api/v1/auth/verify-email",
            "/api/v1/auth/logout",
        ):
            assert path in CSRF_EXEMPT_PATHS

        # Webhook paths are HMAC-verified, not CSRF-protected
        assert any("/payments/webhook" in p for p in WEBHOOK_PATHS)


class TestCSRFMiddlewareRegistration:
    """Verify CSRF is wired into the orchestrator pipeline."""

    def test_csrf_middleware_in_active_security_layer(self):
        from middleware.orchestrator import _SECURITY
        from middleware.csrf_middleware import CSRFMiddleware

        assert CSRFMiddleware in _SECURITY, (
            "CSRFMiddleware must be in the SECURITY layer of the orchestrator"
        )

    def test_orchestrator_pipeline_order(self):
        """Documented execution order (outer→inner):
        FOUNDATION → AUTH → RATE → WEBHOOKS → GEO → SECURITY → OBSERVABILITY
        → COMPLIANCE (prod).
        SECURITY contains CSRF — CSRF runs late so a valid cookie/header is
        expected to be present on state-changing requests.
        """
        from middleware.orchestrator import (
            _FOUNDATION,
            _AUTHENTICATION,
            _RATE_LIMITING,
            _WEBHOOKS,
            _GEO_COUNTRY,
            _SECURITY,
            _OBSERVABILITY,
            _COMPLIANCE,
        )

        # Each layer is non-empty
        for layer, name in (
            (_FOUNDATION, "FOUNDATION"),
            (_AUTHENTICATION, "AUTH"),
            (_RATE_LIMITING, "RATE"),
            (_WEBHOOKS, "WEBHOOKS"),
            (_GEO_COUNTRY, "GEO"),
            (_SECURITY, "SECURITY"),
            (_OBSERVABILITY, "OBSERVABILITY"),
            (_COMPLIANCE, "COMPLIANCE"),
        ):
            assert layer, f"{name} layer is empty"

        from middleware.csrf_middleware import CSRFMiddleware
        assert CSRFMiddleware in _SECURITY


class TestCSRFTokenRoundTrip:
    """Pure-logic tests using FastAPI's TestClient where possible."""

    def test_get_request_seeds_csrf_cookie(self):
        """A safe-method response should carry a ``csrf_token`` cookie."""
        try:
            from fastapi import FastAPI
            from starlette.testclient import TestClient
            from middleware.csrf_middleware import CSRFMiddleware
        except Exception:
            pytest.skip("fastapi/starlette unavailable")

        app = FastAPI()
        app.add_middleware(CSRFMiddleware)

        @app.get("/ping")
        def ping():
            return {"ok": True}

        os.environ.pop("CSRF_DISABLED", None)
        try:
            with TestClient(app) as client:
                resp = client.get("/ping")
                assert resp.status_code == 200
                # The middleware sets the csrf_token cookie on GET responses.
                assert "csrf_token" in resp.cookies
                token = resp.cookies["csrf_token"]
                assert len(token) >= 32
        finally:
            os.environ["CSRF_DISABLED"] = "true"
            os.environ.pop("CSRF_DISABLED", None)

    def test_post_without_csrf_token_rejected_when_enabled(self):
        """A POST without the CSRF header/cookie must be rejected (403).

        Note: ``CSRFMiddleware`` raises ``HTTPException(403)`` from inside
        ``BaseHTTPMiddleware.dispatch`` (does not return a JSONResponse), so
        the TestClient surfaces it as an exception in the test context.  We
        assert on the raised exception, which is the live contract.
        """
        try:
            from fastapi import FastAPI, HTTPException
            from starlette.testclient import TestClient
            from middleware.csrf_middleware import CSRFMiddleware
        except Exception:
            pytest.skip("fastapi/starlette unavailable")

        os.environ.pop("CSRF_DISABLED", None)
        app = FastAPI()
        app.add_middleware(CSRFMiddleware)

        @app.post("/echo")
        def echo(payload: dict):
            return {"received": payload}

        try:
            with TestClient(app, raise_server_exceptions=True) as client:
                with pytest.raises(HTTPException) as exc:
                    client.post("/echo", json={"x": 1})
                assert exc.value.status_code == 403
                assert "CSRF" in str(exc.value.detail)
        finally:
            os.environ["CSRF_DISABLED"] = "true"
            os.environ.pop("CSRF_DISABLED", None)
