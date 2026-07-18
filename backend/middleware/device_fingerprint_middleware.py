"""Device fingerprint middleware.

Extracts a stable device fingerprint from request headers and attaches it to
``request.state.device_fingerprint``.  The fingerprint is a SHA-256 hash of
User-Agent, Accept-Language, Sec-CH-UA-* hints and the optional X-Device-ID
header.
"""

from __future__ import annotations

import hashlib
import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger(__name__)

_FINGERPRINT_HEADERS = (
    "user-agent",
    "accept-language",
    "sec-ch-ua",
    "sec-ch-ua-platform",
    "sec-ch-ua-mobile",
)


def compute_device_fingerprint(request: Request) -> str | None:
    """Return a SHA-256 hex digest of available device signal headers."""
    parts: list[str] = []
    for name in _FINGERPRINT_HEADERS:
        value = request.headers.get(name)
        if value:
            parts.append(f"{name}={value}")

    explicit_id = request.headers.get("X-Device-ID", "").strip()
    if explicit_id:
        parts.append(f"x-device-id={explicit_id}")

    if not parts:
        return None

    raw = "|".join(parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class DeviceFingerprintMiddleware(BaseHTTPMiddleware):
    """Attach device fingerprint to ``request.state.device_fingerprint``."""

    async def dispatch(self, request: Request, call_next):
        fp = compute_device_fingerprint(request)
        request.state.device_fingerprint = fp
        response = await call_next(request)
        if fp:
            response.headers.setdefault("X-Device-Fingerprint", fp[:16])
        return response

