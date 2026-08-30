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
│ 3.5 WEBHOOKS      IP whitelist + HMAC verification │
├───────────────────────────────────────────────────────────────┤
│ 4. GEO & COUNTRY  Country resolution              │
├───────────────────────────────────────────────────────────────┤
│ 5. COMPLIANCE     PCI-DSS audit (production only) │
╰───────────────────────────────────────────────────────────────╯

Registration order is reversed at registration time to compensate for
Starlette's ``add_middleware`` prepend behaviour (see ``setup_middleware``).
Only middleware that was previously registered is active.  Additional
middleware exists in the codebase but is listed as COMMENTED-OUT entries —
review and uncomment deliberately; each has behavioral consequences.

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
from middleware.impossible_travel_middleware import (
    ImpossibleTravelMiddleware,
    FraudDetectionMiddleware,
    FraudScoringMiddleware,
)
from middleware.rate_limit_middleware import RateLimitMiddleware
from middleware.pci_dss_compliance import PCIDSSMiddleware
from middleware.request_id_middleware import RequestIDMiddleware
from middleware.csrf_middleware import CSRFMiddleware
from middleware.logging_middleware import RequestLoggingMiddleware
from middleware.api_version_middleware import ApiVersionMiddleware
from middleware.authentication_middleware import AuthenticationMiddleware
from middleware.device_binding_middleware import DeviceBindingMiddleware
from middleware.webhook_verification import WebhookVerificationMiddleware
from middleware.webhook_ip_whitelist import WebhookIPWhitelistMiddleware

from infrastructure.utils.config import settings

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Layer 1: Foundation — bare-minimum request plumbing
# ──────────────────────────────────────────────

_FOUNDATION: list[type] = [
    GZipMiddleware,              # Original pos 1 — built-in gzip compression
    IPExtractionMiddleware,      # Original pos 3 — extract & store client IP
    RequestIDMiddleware,         # Generates/preserves X-Request-ID for tracing
    ApiVersionMiddleware,         # Extracts API version from headers
]

# ──────────────────────────────────────────────
# Layer 2: Authentication — Resolve user from JWT
# MUST run BEFORE Geo & Country so that RLS scope can be
# derived from the authenticated user's identity
# ──────────────────────────────────────────────

_AUTHENTICATION: list[type] = [
    AuthenticationMiddleware,  # Resolve user from JWT, populate request.state
    DeviceBindingMiddleware,   # Bind device fingerprint to request.state
]

# ──────────────────────────────────────────────
# Layer 3: Rate Limiting — EARLY DoS protection
# MUST run BEFORE expensive security/DB operations
# ──────────────────────────────────────────────

_RATE_LIMITING: list[type] = [
    RateLimitMiddleware,  # Sliding-window per-path limiter
]

# ──────────────────────────────────────────────
# Layer 3.5: Webhook Guards — IP whitelist + HMAC verification
# MUST run AFTER Rate Limiting (avoid spending crypto verification
# cycles on rate-limited callers) and BEFORE Geo & Country (so
# unverified, non-whitelisted webhook traffic is rejected before
# country/RLS lookups).
# ──────────────────────────────────────────────

_WEBHOOKS: list[type] = [
    WebhookIPWhitelistMiddleware,   # Reject non-whitelisted source IPs
    WebhookVerificationMiddleware,  # HMAC signature verification
]

# ──────────────────────────────────────────────
# Layer 4: Geo & Country — Set RLS scope
# MUST run AFTER Authentication so request.state.user is populated
# MUST run BEFORE any middleware that opens DB sessions
# ──────────────────────────────────────────────

_GEO_COUNTRY: list[type] = [
    CountryContextMiddleware,  # Resolve country code and set RLS scope

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
# Layer 6: PCI Compliance (production only)
# ──────────────────────────────────────────────

_COMPLIANCE: list[type] = [
    PCIDSSMiddleware,  # PCI-DSS audit & HTTPS enforcement
]

# ──────────────────────────────────────────────
# Layer 7: Security (runs WITH proper RLS scope + user context)
# ──────────────────────────────────────────────

_SECURITY: list[type] = [
    EnhancedSecurityHeadersMiddleware,  # CSP, HSTS, etc.
    ImpossibleTravelMiddleware,         # Geo-impossible travel
    FraudDetectionMiddleware,           # Fraud detection
    FraudScoringMiddleware,             # Fraud scoring
    CSRFMiddleware,                     # CSRF protection
]


def setup_middleware(app: FastAPI) -> None:
    """Register the middleware pipeline on *app*.

    Starlette's :meth:`~fastapi.FastAPI.add_middleware` **prepends** each new
    middleware (it inserts at index 0 of its internal list), so the *last*
    middleware registered becomes the **outermost** and runs first on the way
    in.  To honour the documented outer→inner order below, the ordered
    pipeline is therefore registered in **reverse**.

    Documented execution order (outermost first, i.e. closest to the client):
        FOUNDATION → AUTHENTICATION → RATE LIMITING → WEBHOOKS
        → GEO & COUNTRY → SECURITY → OBSERVABILITY
        → COMPLIANCE (production only)

    Authentication MUST run before Geo & Country so that CountryContextMiddleware
    can read request.state.user (populated by AuthenticationMiddleware) to
    resolve the RLS country scope from the authenticated user's identity.
    """
    pipeline: list[type] = [
        *_FOUNDATION,
        *_AUTHENTICATION,
        *_RATE_LIMITING,
        *_WEBHOOKS,
        *_GEO_COUNTRY,
        *_SECURITY,
        *_OBSERVABILITY,
    ]

    app_env = str(getattr(settings, "app_env", "") or "").lower()
    if app_env not in ("test", "development"):
        pipeline = [*pipeline, *_COMPLIANCE]

    # Register in reverse: because Starlette prepends, the first entry in
    # ``pipeline`` (FOUNDATION) ends up outermost after all insertions.
    for mw in reversed(pipeline):
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
    layers = [_FOUNDATION, _AUTHENTICATION, _RATE_LIMITING, _WEBHOOKS,
              _GEO_COUNTRY, _SECURITY, _OBSERVABILITY, _COMPLIANCE]
    return sum(1 for layer in layers if layer)


def _total_middleware() -> int:
    """Total middleware classes across all layers."""
    layers = [_FOUNDATION, _AUTHENTICATION, _RATE_LIMITING, _WEBHOOKS,
              _GEO_COUNTRY, _SECURITY, _OBSERVABILITY, _COMPLIANCE]
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
# ║  services/security/        │  BehavioralAnalyzer   │  UTILITY  ║
# ║    behavioral_analytics.py │  (relocated)          │          ║
# ║  coi_middleware.py         │  COIMiddleware        │  UTILITY  ║
# ║  database_security.py      │  DatabaseSecurityMgr  │  UTILITY  ║
# ║  services/security/        │  SIEMEngine          │  UTILITY  ║
# ║    siem_engine.py          │  (relocated)          │          ║
# ║  webhook_verification.py   │  WebhookVerification  │  ACTIVE   ║
# ║  webhook_ip_whitelist.py  │  WebhookIPWhitelist   │  ACTIVE   ║
# ║  device_binding_middleware │  DeviceBindingMw     │  ALIAS    ║
# ╚═══════════════════════════════════════════════════════════════╝

