from __future__ import annotations

import os
import secrets
import logging
from typing import Optional
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from infrastructure.utils.config import settings

logger = logging.getLogger(__name__)

CSRF_TOKEN_LENGTH = 32
CSRF_COOKIE_NAME = "csrf_token"
CSRF_HEADER_NAME = "X-CSRF-Token"

STATEFUL_METHODS = frozenset({"POST", "PUT", "DELETE", "PATCH"})

WEBHOOK_PATHS = {
    "/payments/webhook",
    "/payments/tap/webhook",
    "/email/webhooks",
}

# Auth endpoints that don't require CSRF protection (public endpoints)
CSRF_EXEMPT_PATHS = {
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/auth/refresh",
    "/api/v1/auth/logout",
    "/api/v1/auth/forgot-password",
    "/api/v1/auth/reset-password",
    "/api/v1/auth/verify-email",
    "/api/v1/auth/me",
}


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    CSRF protection using double-submit cookie pattern.

    The client must send the CSRF token in a header (X-CSRF-Token) and also
    receive it in a cookie. The server compares both values.

    For the JS client to echo the cookie back as a header, the cookie must be
    readable by JavaScript, so it is set with httponly=False. SameSite=Lax still
    prevents the cookie from being sent on cross-site requests."""

    async def dispatch(self, request: Request, call_next):
        # Allow disabling CSRF for tests and development
        csrf_disabled = os.environ.get("CSRF_DISABLED", "").lower() in ("true", "1", "yes")
        logger.info(f"CSRF middleware: CSRF_DISABLED={os.environ.get('CSRF_DISABLED')}, disabled={csrf_disabled}, path={request.url.path}")
        if csrf_disabled:
            return await call_next(request)

        if request.method == "OPTIONS":
            return await call_next(request)

        # Exempt auth endpoints from CSRF protection
        if request.url.path in CSRF_EXEMPT_PATHS:
            return await call_next(request)

        if request.method not in STATEFUL_METHODS:
            response = await call_next(request)
            # Ensure CSRF cookie is set on GET requests so clients have it ready for POST
            if not self._is_csrf_cookie_set(request):
                self._set_csrf_cookie(response, generate_csrf_token())
            return response

        if any(request.url.path.startswith(w) for w in WEBHOOK_PATHS):
            return await call_next(request)

        client_token = request.headers.get(CSRF_HEADER_NAME)

        if not client_token:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF token missing. Include X-CSRF-Token header.",
            )

        cookie_token = request.cookies.get(CSRF_COOKIE_NAME)

        if not cookie_token:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF cookie missing. Ensure cookies are enabled.",
            )

        if not self._constant_time_compare(client_token, cookie_token):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF token mismatch.",
            )

        response = await call_next(request)

        if not self._is_csrf_cookie_set(request):
            self._set_csrf_cookie(response, client_token)

        return response

    def _set_csrf_cookie(self, response, token: str) -> None:
        is_production = str(getattr(settings, "app_env", "development")).lower() == "production"
        response.set_cookie(
            key=CSRF_COOKIE_NAME,
            value=token,
            httponly=False,
            secure=is_production,
            samesite="lax",
            max_age=3600,
            path="/",
        )

    def _constant_time_compare(self, a: str, b: str) -> bool:
        """Constant-time string comparison to prevent timing attacks."""
        return secrets.compare_digest(
            a.encode("utf-8"),
            b.encode("utf-8")
        )

    def _is_csrf_cookie_set(self, request: Request) -> bool:
        return CSRF_COOKIE_NAME in request.cookies


def generate_csrf_token() -> str:
    """Generate a new CSRF token."""
    return secrets.token_hex(CSRF_TOKEN_LENGTH)


def get_csrf_token_from_request(request: Request) -> Optional[str]:
    """Extract CSRF token from request (cookie or header)."""
    return request.cookies.get(CSRF_COOKIE_NAME) or request.headers.get(CSRF_HEADER_NAME)

