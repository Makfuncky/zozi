"""FastAPI auth dependencies — backward-compat shim.

Canonical implementation lives in
``domains.accounts.services.auth.security_dependencies``.
All auth flows through ``infrastructure.utils.auth`` (decode_token / verify_token).

This module uses lazy resolution to avoid a static upward import (Law 1).
"""
from __future__ import annotations

import functools
import importlib as _importlib
from contextvars import ContextVar
from typing import Optional

_SOURCE = "domains.accounts.services.auth.security_dependencies"

_current_user_ctx: ContextVar = ContextVar("_current_user_ctx", default=None)


def set_current_user(user):
    """Set the current user in the context variable. Called by auth dependencies."""
    _current_user_ctx.set(user)


def verify_captcha(request: Request) -> None:
    """Verify bot-detection challenge token (Cloudflare Turnstile) on public endpoints.

    Skips verification when ``TURNSTILE_SECRET_KEY`` is not configured, preserving
    development and test workflows. In production, a missing or invalid token
    results in ``HTTP 400``.
    """
    from fastapi import HTTPException, status

    import os

    secret_key = os.getenv("TURNSTILE_SECRET_KEY", "").strip()
    if not secret_key:
        return

    content_type = request.headers.get("content-type", "")
    token: Optional[str] = None

    if "application/json" in content_type:
        try:
            import json as _json
            body = _json.loads(request._body or b"{}")
            token = body.get("captcha_token") or body.get("turnstile_token")
        except Exception:
            token = None
    else:
        form = getattr(request, "_form", None)
        if form is None:
            try:
                import asyncio
                form = asyncio.run(request.form())
            except Exception:
                form = None
        if form is not None:
            token = form.get("captcha_token") or form.get("turnstile_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CAPTCHA token is required",
        )

    try:
        import urllib.request as _urllib_request
        import urllib.parse as _urllib_parse

        data = _urllib_parse.urlencode({
            "secret": secret_key,
            "response": token,
            "remoteip": request.client.host if request.client else None,
        }).encode()

        req = _urllib_request.Request(
            "https://challenges.cloudflare.com/turnstile/v0/siteverify",
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        with _urllib_request.urlopen(req, timeout=5) as resp:
            result = __import__("json").loads(resp.read().decode())
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"CAPTCHA verification failed: {exc}",
        ) from exc

    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CAPTCHA verification failed",
        )


def _mask_email(email: Optional[str]) -> str:
    """Mask an email address for PII-safe responses."""
    if not email or "@" not in email:
        return email or ""
    local, domain = email.split("@", 1)
    return f"{local[0]}***@{domain}"


def __getattr__(name: str):
    mod = _importlib.import_module(_SOURCE)
    value = getattr(mod, name)
    # Ensure every resolved user is published to the rbac context var so that
    # feature/module gates (which read the current user from request context)
    # work for both ``Depends(...)`` and direct in-handler ``require_feature``
    # calls. Lazy import keeps the upward edge out of the static import graph.
    if name == "get_current_user":
        _orig = value

        @functools.wraps(_orig)
        def _wrapped(*args, **kwargs):
            # Lazy import kept inside the call to avoid a circular import at
            # module load time (rbac.dependencies imports this shim).
            user = _orig(*args, **kwargs)
            try:
                set_current_user(user)
            except Exception:
                pass
            return user

        value = _wrapped
    globals()[name] = value
    return value
