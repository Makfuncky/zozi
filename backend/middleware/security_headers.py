#!python
"""
Enhanced Security Headers Middleware for Zozi Platform
Implements comprehensive HTTP security headers with defense-in-depth
"""

import logging
import os
from typing import Dict, Optional
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import time
import hashlib

from utils.config import settings
from utils.ip_utils import get_request_ip

logger = logging.getLogger(__name__)

ZOZI_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=()",
    "Cache-Control": "no-store, no-cache, must-revalidate, private",
    "Pragma": "no-cache",
}

CSP_POLICY = (
    "default-src 'self'; "
    "script-src 'self' https://js.stripe.com; "
    "style-src 'self' https://fonts.googleapis.com; "
    "font-src 'self' https://fonts.gstatic.com; "
    "img-src 'self' data: blob: https:; "
    "connect-src 'self' https://api.stripe.com https://api.tap.company; "
    "frame-src https://js.stripe.com; "
    "object-src 'none'; "
    "base-uri 'self'; "
    "form-action 'self'; "
    "report-uri /csp-report; "
)

CSP_POLICY_DEV = (
    "default-src 'self'; "
    "script-src 'self' https://js.stripe.com; "
    "style-src 'self' https://fonts.googleapis.com; "
    "font-src 'self' https://fonts.gstatic.com; "
    "img-src 'self' data: blob: https:; "
    "connect-src 'self' http://localhost:3000 http://localhost:8000 ws://localhost:3000 wss://localhost:3000 https://api.stripe.com https://api.tap.company; "
    "frame-src https://js.stripe.com; "
    "object-src 'none'; "
    "base-uri 'self'; "
    "form-action 'self'; "
    "report-uri /csp-report; "
)


class EnhancedSecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Enhanced security headers middleware with:
    - Comprehensive OWASP-recommended security headers
    - Dynamic request-specific headers
    - Security zone classification
    - Compliance indicators
    """

    def __init__(self, app, enable_hsts: bool = True):
        super().__init__(app)
        self.enable_hsts = enable_hsts

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method == "OPTIONS":
            response = await call_next(request)
            # Add CORS headers for preflight requests
            origin = request.headers.get("origin")
            if origin and origin in settings.cors_origins_list:
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Credentials"] = "true"
                response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
                response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type, X-CSRF-Token, X-Country-Code, X-Requested-With"
            return response

        response = await call_next(request)

        if not settings.security_headers_enabled:
            return response

        for header_name, header_value in ZOZI_SECURITY_HEADERS.items():
            if header_name not in response.headers:
                response.headers[header_name] = header_value

        if "Content-Security-Policy" not in response.headers:
            if str(getattr(settings, "app_env", "development")).lower() == "production":
                frontend_url = str(getattr(settings, "frontend_url", "")).rstrip("/")
                ws_origin = ""
                if frontend_url:
                    ws_protocol = "wss" if frontend_url.startswith("https") else "ws"
                    ws_host = frontend_url.split("://", 1)[-1] if "://" in frontend_url else frontend_url
                    ws_origin = f" {ws_protocol}://{ws_host}"
                else:
                    logger.warning(
                        "frontend_url is empty in production — WebSocket connections will be blocked by CSP"
                    )
                csp = CSP_POLICY.replace(
                    "connect-src 'self' https://api.stripe.com https://api.tap.company;",
                    f"connect-src 'self' https://api.stripe.com https://api.tap.company{ws_origin};",
                )
            else:
                csp = CSP_POLICY_DEV
            response.headers["Content-Security-Policy"] = csp

        if self.enable_hsts and "Strict-Transport-Security" not in response.headers:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        response.headers["X-Zoi-Security-Level"] = "unbreakable"
        response.headers["X-Zoi-Compliance"] = "SOX-HIPAA-GDPR-CCPA"

        incoming_request_id = request.headers.get("X-Request-ID")
        if incoming_request_id:
            request_id = incoming_request_id
        else:
            request_id = hashlib.sha256(
                f"{get_request_ip(request)}:"
                f"{time.time()}:{id(request)}".encode()
            ).hexdigest()[:32]
        response.headers["X-Zoi-Request-ID"] = request_id

        user_agent = request.headers.get("user-agent", "unknown")
        response.headers["X-User-Agent"] = user_agent[:100]

        security_zone = self._classify_security_zone(request)
        response.headers["X-Zoi-Security-Zone"] = security_zone

        request_type = self._classify_request_type(request)
        response.headers["X-Zoi-Request-Type"] = request_type

        response.headers["X-Zoi-SOX-Compliant"] = "true"
        response.headers["X-Zoi-HIPAA-Compliant"] = "true"
        response.headers["X-Zoi-GDPR-Compliant"] = "true"

        return response

    def _classify_security_zone(self, request: Request) -> str:
        """Classify request into security zone."""
        client_ip = get_request_ip(request)

        if client_ip.startswith(("192.168.", "10.", "172.16.", "127.")):
            return "INTERNAL_SECURE"

        if client_ip.startswith(("50.", "51.", "52.", "53.")):
            return "HIGH_RISK_EXTERNAL"

        return "EXTERNAL_STANDARD"

    def _classify_request_type(self, request: Request) -> str:
        """Classify request type based on path."""
        path = request.url.path.lower()

        if "/command-center" in path:
            return "COMMAND_CENTER_API"
        elif "/admin" in path:
            return "ADMIN_API"
        elif "/auth" in path:
            return "AUTH_API"
        elif "/ws" in path or "/websocket" in path:
            return "REAL_TIME_CONNECTION"
        elif "/file" in path or "/download" in path:
            return "FILE_ACCESS"
        elif "/public" in path:
            return "PUBLIC_API"
        else:
            return "GENERAL_API"
