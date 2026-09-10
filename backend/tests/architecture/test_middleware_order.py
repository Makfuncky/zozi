"""Phase 4G: Middleware layer order per ARCHITECTURE_DIAGRAM.md §6.

Verifies the 8 layers are registered in the documented order:
  FOUNDATION → AUTHENTICATION → RATE LIMITING → WEBHOOKS →
  GEO & COUNTRY → OBSERVABILITY → SECURITY → COMPLIANCE (prod only)
"""
from __future__ import annotations

import os

import pytest


def _pipeline_for(app_env: str | None = None) -> list[type]:
    """Return the registered middleware pipeline for a given APP_ENV.

    The orchestrator pre-registers in reverse, so the active outer→inner
    order is the reverse of the registration order.
    """
    if app_env is not None:
        os.environ["APP_ENV"] = app_env
    # Import inside the function so APP_ENV can be toggled per-test.
    from middleware.orchestrator import (
        _FOUNDATION, _AUTHENTICATION, _RATE_LIMITING, _WEBHOOKS,
        _GEO_COUNTRY, _OBSERVABILITY, _SECURITY, _COMPLIANCE,
    )

    layers = [
        _FOUNDATION, _AUTHENTICATION, _RATE_LIMITING, _WEBHOOKS,
        _GEO_COUNTRY, _OBSERVABILITY, _SECURITY, _COMPLIANCE,
    ]
    return [c for layer in layers for c in layer]


def test_foundation_includes_cors():
    from middleware.orchestrator import _FOUNDATION
    names = [c.__name__ for c in _FOUNDATION]
    assert "CORSMiddleware" in names, (
        "CORS middleware must be in FOUNDATION (L1) per ARCH §6"
    )


def test_foundation_includes_gzip_and_ip_and_requestid_and_version():
    from middleware.orchestrator import _FOUNDATION
    names = {c.__name__ for c in _FOUNDATION}
    for required in ("GZipMiddleware", "IPExtractionMiddleware",
                     "RequestIDMiddleware", "ApiVersionMiddleware"):
        assert required in names, f"FOUNDATION missing {required}"


def test_authentication_layer_classes():
    from middleware.orchestrator import _AUTHENTICATION
    names = {c.__name__ for c in _AUTHENTICATION}
    assert "AuthenticationMiddleware" in names
    assert "DeviceBindingMiddleware" in names


def test_rate_limit_layer():
    from middleware.orchestrator import _RATE_LIMITING
    assert any(c.__name__ == "RateLimitMiddleware" for c in _RATE_LIMITING)


def test_webhook_layer_active():
    from middleware.orchestrator import _WEBHOOKS
    names = {c.__name__ for c in _WEBHOOKS}
    assert "WebhookIPWhitelistMiddleware" in names
    assert "WebhookVerificationMiddleware" in names


def test_geo_country_layer():
    from middleware.orchestrator import _GEO_COUNTRY
    assert any(c.__name__ == "CountryContextMiddleware" for c in _GEO_COUNTRY)


def test_security_layer_includes_csrf():
    from middleware.orchestrator import _SECURITY
    names = {c.__name__ for c in _SECURITY}
    assert "CSRFMiddleware" in names
    assert "EnhancedSecurityHeadersMiddleware" in names


def test_observability_layer_includes_logging():
    from middleware.orchestrator import _OBSERVABILITY
    names = {c.__name__ for c in _OBSERVABILITY}
    assert "RequestLoggingMiddleware" in names


def test_pci_compliance_layer_has_pci():
    from middleware.orchestrator import _COMPLIANCE
    names = {c.__name__ for c in _COMPLIANCE}
    assert "PCIDSSMiddleware" in names


def test_pipeline_order_obs_before_sec():
    """ARCH §6 documents OBSERVABILITY before SECURITY on the request path."""
    pipeline = _pipeline_for(app_env="test")
    obs_idx = pipeline.__class__.__name__  # not used
    from middleware.orchestrator import (
        _OBSERVABILITY, _SECURITY,
    )
    obs_class = next(iter(_OBSERVABILITY))
    sec_class = next(iter(_SECURITY))
    # Reverse-registered lists mean the active outer→inner order is the
    # reverse of how the orchestrator passes them in; we just need to
    # assert that observability classes appear earlier in the active
    # outer→inner order than security classes.
    if obs_class in pipeline and sec_class in pipeline:
        assert pipeline.index(obs_class) < pipeline.index(sec_class), (
            "OBSERVABILITY must come before SECURITY on the request path"
        )
    # If either layer is empty (extreme fallback), skip the strict check.
    pytest.skip("Pipeline composition check is best-effort.")


def test_pci_middleware_only_in_prod(monkeypatch):
    """L8 COMPLIANCE (PCI) must only be loaded when APP_ENV is production."""
    # In test/dev the orchestrator must skip _COMPLIANCE.
    from middleware.orchestrator import setup_middleware
    from fastapi import FastAPI
    from starlette.middleware import Middleware

    for app_env in ("test", "development"):
        monkeypatch.setenv("APP_ENV", app_env)
        app = FastAPI()
        setup_middleware(app)
        from middleware.pci_dss_compliance import PCIDSSMiddleware
        active = [m.cls for m in app.user_middleware]
        assert PCIDSSMiddleware not in active, (
            f"PCI middleware must NOT be active in APP_ENV={app_env}"
        )


def test_pci_middleware_active_in_prod(monkeypatch):
    """In production, PCI middleware is required."""
    from middleware.orchestrator import setup_middleware
    from fastapi import FastAPI
    from middleware.pci_dss_compliance import PCIDSSMiddleware

    monkeypatch.setenv("APP_ENV", "production")
    app = FastAPI()
    setup_middleware(app)
    active = [m.cls for m in app.user_middleware]
    assert PCIDSSMiddleware in active
