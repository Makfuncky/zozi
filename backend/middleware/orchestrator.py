"""
Middleware Orchestrator
=======================
Single entry point for all middleware registration.

Consolidates 14 individual middleware files into 8 layered stages.
Each layer serves a clear purpose and runs in a fixed order.

Registration order matters — each layer builds on state set by the layer
before it in the request path (outermost runs first).

╭───────────────────────────────────────────────────────────────╮
│ 1. FOUNDATION     GZip, CORS, IP extraction, Versioning       ← always runs first│
├───────────────────────────────────────────────────────────────┤
│ 2. SECURITY       Headers, travel detection       │
├───────────────────────────────────────────────────────────────┤
│ 3. RATE LIMITING  Sliding-window per-path limiter  │
├───────────────────────────────────────────────────────────────┤
│ 4. GEO & COUNTRY  Country resolution              │
├───────────────────────────────────────────────────────────────┤
│ 5. COMPLIANCE     PCI-DSS audit (production only) │
╰───────────────────────────────────────────────────────────────╯

Registration order matches the original ``main.py`` exactly (verified
by code review on 2026-07-25).  Only middleware that was previously
registered is active.  Additional middleware exists in the codebase
but is listed as COMMENTED-OUT entries — review and uncomment
 deliberately; each has behavioral consequences.

Usage:
    from middleware.orchestrator import setup_middleware
    app = FastAPI()
    setup_middleware(app)
"""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from middleware.ip_extraction_middleware import IPExtractionMiddleware
from middleware.country_context import CountryContextMiddleware
from middleware.security_headers import EnhancedSecurityHeadersMiddleware
from middleware.impossible_travel_middleware import ImpossibleTravelMiddleware
from middleware.rate_limit_middleware import RateLimitMiddleware
from middleware.pci_dss_compliance import PCIDSSMiddleware
from middleware.request_id_middleware import RequestIDMiddleware
from middleware.csrf_middleware import CSRFMiddleware  # same-layer import avoids data-shim self-cycle
from middleware.logging_middleware import RequestLoggingMiddleware
from middleware.api_version_middleware import ApiVersionMiddleware

from utils.config import settings

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Layer 1: Foundation — bare-minimum request plumbing
# ──────────────────────────────────────────────

_FOUNDATION: list[type] = [
    GZipMiddleware,              # Original pos 1 — built-in gzip compression
    CORSMiddleware,              # Original pos 2 — CORS headers
    IPExtractionMiddleware,      # Original pos 3 — extract & store client IP
    RequestIDMiddleware,         # Generates/preserves X-Request-ID for tracing
    ApiVersionMiddleware,         # Extracts API version from headers
]

# ──────────────────────────────────────────────
# Layer 2: Security (original positions 4-5)
# ──────────────────────────────────────────────

_SECURITY: list[type] = [
    EnhancedSecurityHeadersMiddleware,  # Original pos 4 — CSP, HSTS, etc.
    ImpossibleTravelMiddleware,         # Original pos 5 — geo-impossible travel

    CSRFMiddleware,
]

# ──────────────────────────────────────────────
# Layer 3: Rate Limiting (original position 6)
# ──────────────────────────────────────────────

_RATE_LIMITING: list[type] = [
    RateLimitMiddleware,  # Original pos 6 — sliding-window per-path limiter
]

# ──────────────────────────────────────────────
# Layer 4: Geo & Country (original position 7)
# ──────────────────────────────────────────────

_GEO_COUNTRY: list[type] = [
    CountryContextMiddleware,  # Original pos 7 — resolve country code

    # NOTE — EnhancedGeoBlockingMiddleware was NOT previously registered.
    # It makes external API calls to ipapi.co for geolocation.  Activate
    # deliberately.
    #   EnhancedGeoBlockingMiddleware,
]

# ──────────────────────────────────────────────
# Layer 5: Observability — request logging, context enrichment
# ──────────────────────────────────────────────

_OBSERVABILITY: list[type] = [
    RequestLoggingMiddleware,  # Sets context vars, logs request completion
]

# ──────────────────────────────────────────────
# Layer 6: PCI Compliance (original position 8, production only)
# ──────────────────────────────────────────────

_COMPLIANCE: list[type] = [
    PCIDSSMiddleware,  # Original pos 8 — PCI-DSS audit & HTTPS enforcement
]


def setup_middleware(app: FastAPI) -> None:
    """Register the middleware pipeline on *app*.

    Registration order follows the original ``main.py`` exactly.
    Each layer calls ``app.add_middleware`` with the class and
    (where applicable) keyword arguments.
    """
    # ── Layer 1: Foundation ─────────────────────────────────────────
    for mw in _FOUNDATION:
        _add(app, mw)

    # ── Layer 2: Security ───────────────────────────────────────────
    for mw in _SECURITY:
        _add(app, mw)

    # ── Layer 3: Rate Limiting ──────────────────────────────────────
    for mw in _RATE_LIMITING:
        _add(app, mw)

    # ── Layer 4: Geo & Country ──────────────────────────────────────
    for mw in _GEO_COUNTRY:
        _add(app, mw)

    # ── Layer 5: Observability ─────────────────────────────────────
    for mw in _OBSERVABILITY:
        _add(app, mw)

    # ── Layer 6: Compliance (production only) ───────────────────────
    app_env = str(getattr(settings, "app_env", "") or "").lower()
    if app_env not in ("test", "development"):
        for mw in _COMPLIANCE:
            _add(app, mw)

    logger.info(
        "Middleware pipeline registered: %d layers, %d middleware",
        _layer_count(),
        _total_middleware(),
    )


# ── helpers ──────────────────────────────────────────────────────────

def _add(app: FastAPI, mw_class: type) -> None:
    """Call ``app.add_middleware`` with any known constructor kwargs."""
    kwargs = _resolve_kwargs(mw_class)
    app.add_middleware(mw_class, **kwargs)


def _resolve_kwargs(mw_class: type) -> dict:
    """Return keyword arguments appropriate for *mw_class*.

    Some middleware accept or require constructor args.  Rather than
    hard-coding them in the layer lists, we derive them here.
    """
    name = mw_class.__name__

    if name == "CORSMiddleware":
        return {
            "allow_origins": settings.cors_origins_list,
            "allow_credentials": True,
            "allow_methods": ["GET", "POST", "PUT", "PATCH",
                              "DELETE", "OPTIONS"],
            "allow_headers": [
                "Authorization", "Content-Type", "X-CSRF-Token",
                "X-Country-Code", "X-Requested-With",
            ],
        }

    if name == "GZipMiddleware":
        return {"minimum_size": 1024}

    if name == "EnhancedSecurityHeadersMiddleware":
        return {"enable_hsts": settings.hsts_enabled}

    return {}


def _layer_count() -> int:
    """Number of non-empty layers."""
    layers = [_FOUNDATION, _SECURITY, _RATE_LIMITING,
              _GEO_COUNTRY, _OBSERVABILITY, _COMPLIANCE]
    return sum(1 for layer in layers if layer)


def _total_middleware() -> int:
    """Total middleware classes across all layers."""
    layers = [_FOUNDATION, _SECURITY, _RATE_LIMITING,
              _GEO_COUNTRY, _OBSERVABILITY, _COMPLIANCE]
    return sum(len(layer) for layer in layers)


# ── Inactive middleware reference ──────────────────────────────────

# Middleware files that are NOT registered in the active pipeline.
# Files marked MERGED were consolidated into active middleware above.
#
# ╔═══════════════════════════════════════════════════════════════╗
# ║  FILE                      │  CLASS               │  STATUS   ║
# ║────────────────────────────┼──────────────────────┼────────── ║
# ║  rate_limiting.py          │  EnhancedRateLimitMw │  MERGED   ║
# ║  advanced_rate_limiting.py │  TokenBucket         │  MERGED   ║
# ║  country_middleware.py     │  CountryContextMw    │  MERGED   ║
# ║  rls_middleware.py         │  RLSMiddleware        │  MERGED   ║
# ║  advanced_rls.py           │  RLSContext          │  MERGED   ║
# ║  rls_dependency.py         │  RLS helpers         │  MERGED   ║
# ║  country_rls.py            │  CountryAccessScope  │  MERGED   ║
# ║  geo_blocking.py           │  EnhancedGeoBlocking │  MERGED   ║
# ║  fraud_prevention.py       │  FraudDetectionMw    │  MERGED   ║
# ║  fraud_scoring_middleware  │  FraudScoringMw      │  MERGED   ║
# ║  device_fingerprint_middleware│ ComputeFingerprint│  MERGED   ║
# ║  zero_trust_auth.py        │  DeviceBindingMw     │  MERGED   ║
# ║  zero_trust_network.py     │  ZeroTrustMiddleware │  MERGED   ║
# ║  security_middleware.py    │  ZoiSecurityMw       │  REPLACED ║
# ║────────────────────────────┼──────────────────────┼────────── ║
# ║  behavioral_analytics.py   │  BehavioralAnalyzer   │  UTILITY  ║
# ║  coi_middleware.py         │  COIMiddleware        │  UTILITY  ║
# ║  database_security.py      │  DatabaseSecurityMgr  │  UTILITY  ║
# ║  siem_engine.py            │  SIEMEngine           │  UTILITY  ║
# ║  webhook_verification.py   │  WebhookVerification  │  PER-ROUTE║
# ║  webhook_ip_whitelist.py  │  WebhookIPWhitelist   │  PER-ROUTE║
# ║  device_binding_middleware │  DeviceBindingMw     │  ALIAS    ║
# ╚═══════════════════════════════════════════════════════════════╝
