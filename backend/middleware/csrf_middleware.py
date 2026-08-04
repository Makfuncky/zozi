from __future__ import annotations
import os
import secrets
import hashlib
import logging
from typing import Optional
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from utils.config import settings

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


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    CSRF protection using double-submit cookie pattern.
    
    The client must send the CSRF token in a header (X-CSRF-Token) and also
    receive it in a cookie. The server compares both values.
    
    For same-site applications, this is secure because JavaScript cannot
    access cookies with SameSite=Strict/Lax.
    """

    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS":
            return await call_next(request)

        if request.method not in STATEFUL_METHODS:
            return await call_next(request)

        if any(request.url.path.startswith(w) for w in WEBHOOK_PATHS):
            return await call_next(request)

        app_env = str(getattr(settings, "app_env", "development")).lower()
        csrf_disabled = os.environ.get("CSRF_DISABLED", "").lower() in {"1", "true", "yes"}
        if csrf_disabled:
            logger.warning(
                f"CSRF protection is DISABLED via CSRF_DISABLED env var. "
                "This should NEVER be enabled in production."
            )
            return await call_next(request)

        if app_env in ("test", "development"):
            logger.warning(
                f"CSRF validation in {app_env} mode for {request.method} {request.url.path}. "
                "Consider setting CSRF_DISABLED=true in test environment if needed."
            )

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
            is_production = str(getattr(settings, "app_env", "development")).lower() == "production"
            response.set_cookie(
                key=CSRF_COOKIE_NAME,
                value=client_token,
                httponly=True,
                secure=is_production,
                samesite="strict",
                max_age=3600,
                path="/",
            )

        return response

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
