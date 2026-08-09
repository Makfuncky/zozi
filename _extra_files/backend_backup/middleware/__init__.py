#!python
"""
Zozi Security Middleware Package

Consolidates 31 middleware files into a layered, orchestrated pipeline.

Usage:
    from middleware.orchestrator import setup_middleware
    setup_middleware(app)
"""

from middleware.country_context import CountryContextMiddleware
from middleware.csrf_middleware import CSRFMiddleware
from middleware.orchestrator import setup_middleware
from middleware.pci_dss_compliance import PCIDSSMiddleware
from middleware.rate_limit_middleware import RateLimitMiddleware
from middleware.request_id_middleware import RequestIDMiddleware
from middleware.security_headers import EnhancedSecurityHeadersMiddleware
from middleware.webhook_ip_whitelist import WebhookIPWhitelistMiddleware
from middleware.webhook_verification import WebhookVerificationMiddleware

__all__ = [
    "setup_middleware",
    "EnhancedSecurityHeadersMiddleware",
    "RateLimitMiddleware",
    "CountryContextMiddleware",
    "RequestIDMiddleware",
    "WebhookVerificationMiddleware",
    "WebhookIPWhitelistMiddleware",
    "PCIDSSMiddleware",
    "CSRFMiddleware",
]

__version__ = "4.0.0"

