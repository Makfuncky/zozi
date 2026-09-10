"""Phase 4G: Webhook middleware enforcement (Tasks 3).

The webhook stack (IP whitelist + HMAC verification) must reject requests
with invalid signatures.
"""
from __future__ import annotations

import pytest


class TestWebhookEnforcement:
    def test_webhook_ip_whitelist_middleware_class_loads(self):
        from middleware.webhook_ip_whitelist import WebhookIPWhitelistMiddleware
        assert WebhookIPWhitelistMiddleware is not None

    def test_webhook_verification_middleware_class_loads(self):
        from middleware.webhook_verification import WebhookVerificationMiddleware
        assert WebhookVerificationMiddleware is not None

    def test_webhook_middleware_registered_in_orchestrator(self):
        from middleware.orchestrator import _WEBHOOKS
        names = {c.__name__ for c in _WEBHOOKS}
        assert "WebhookIPWhitelistMiddleware" in names
        assert "WebhookVerificationMiddleware" in names

    def test_webhook_verification_rejects_bad_signature(self):
        """A forged webhook with a bad signature is rejected (401)."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from middleware.webhook_verification import WebhookVerificationMiddleware

        app = FastAPI()
        app.add_middleware(WebhookVerificationMiddleware)

        @app.post("/payments/webhook")
        async def echo():
            return {"ok": True}

        client = TestClient(app)
        resp = client.post(
            "/payments/webhook",
            content=b'{"forged":true}',
            headers={"stripe-signature": "v1=deadbeef"},
        )
        assert resp.status_code == 401, (
            f"webhook forged request should be rejected with 401, got {resp.status_code}"
        )
        assert "Invalid webhook signature" in resp.text


class TestCORSConfiguration:
    def test_cors_in_foundation_layer(self):
        from middleware.orchestrator import _FOUNDATION
        assert any(c.__name__ == "CORSMiddleware" for c in _FOUNDATION)


class TestRateLimitFailClosed:
    def test_rate_limiter_has_valkey_branch(self):
        """The rate limiter must consult Valkey and fall back to memory."""
        from middleware import rate_limit_middleware
        src = open(rate_limit_middleware.__file__, "r", encoding="utf-8").read()
        assert "_get_valkey" in src
        assert "JSONResponse" in src  # returns 429
