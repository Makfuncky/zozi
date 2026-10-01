from __future__ import annotations

import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import structlog
logger = structlog.get_logger(__name__)

logger = logging.getLogger(__name__)


class DeviceBindingMiddleware(BaseHTTPMiddleware):
    """Bind a session to a stable device fingerprint for zero-trust auth.

    Attaches the fingerprint to ``request.state.device_binding`` and echoes a
    truncated binding header on the response.
    """

    async def dispatch(self, request: Request, call_next):
        fingerprint = request.headers.get("X-Device-Fingerprint") or request.headers.get(
            "X-Device-ID"
        )
        request.state.device_binding = fingerprint
        response = await call_next(request)
        if fingerprint:
            response.headers.setdefault("X-Device-Binding", fingerprint[:16])
        return response
