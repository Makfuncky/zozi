"""Request timeout middleware.

Enforces a per-route request timeout to prevent hanging requests from
tying up worker resources.  Uses asyncio cancellation when the route is
async, and falls back to an HTTP 504 (Gateway Timeout) response when the
deadline is exceeded.

Behaviour
---------
* Default timeout: ``REQUEST_TIMEOUT_SECONDS`` (configurable via env).
* Per-route override: any route whose handler is decorated with
  ``@request_timeout(seconds=...)`` wins over the global default.
* Test/development: bypassed entirely so Playwright suites can run
  unhindered.

This middleware is registered in ``middleware.orchestrator`` Layer 1
(Foundation) so it covers every request entering the app.
"""
from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from infrastructure.utils.config import settings

logger = logging.getLogger(__name__)


# Default upper bound for any request (seconds).  Override via
# ``REQUEST_TIMEOUT_SECONDS`` env var.
DEFAULT_REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "30"))


def request_timeout(seconds: float) -> Callable:
    """Decorator: override the default request timeout for one route.

    Use on handler functions:

        @router.get("/expensive")
        @request_timeout(60)
        async def expensive():
            ...
    """
    def _decorator(fn: Callable) -> Callable:
        setattr(fn, "_zozi_request_timeout", float(seconds))
        return fn
    return _decorator


def get_route_timeout(request: Request, default: float) -> float:
    """Return the timeout (seconds) configured for ``request``'s route.

    Falls back to ``default`` when no override is set.  Inspects the
    resolved endpoint on ``request.scope`` (populated by Starlette's
    routing once the path matches).
    """
    endpoint = request.scope.get("endpoint")
    if endpoint is not None:
        override = getattr(endpoint, "_zozi_request_timeout", None)
        if isinstance(override, (int, float)) and override > 0:
            return float(override)
    return default


class RequestTimeoutMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: Callable):
        super().__init__(app)
        self._default_timeout = DEFAULT_REQUEST_TIMEOUT

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        app_env = str(getattr(settings, "app_env", "development")).lower()
        # Bypass in test/development to avoid breaking long Playwright suites.
        if app_env in ("test", "development"):
            return await call_next(request)

        timeout = get_route_timeout(request, self._default_timeout)

        start = time.monotonic()
        try:
            response = await asyncio.wait_for(call_next(request), timeout=timeout)
        except asyncio.TimeoutError:
            elapsed = time.monotonic() - start
            logger.warning(
                "Request timeout after %.1fs: %s %s",
                elapsed,
                request.method,
                request.url.path,
            )
            return JSONResponse(
                status_code=504,
                content={
                    "detail": f"Request exceeded the {int(timeout)}s server timeout",
                    "timeout_seconds": timeout,
                },
            )
        except Exception:
            raise

        return response


__all__ = [
    "RequestTimeoutMiddleware",
    "request_timeout",
    "get_route_timeout",
    "DEFAULT_REQUEST_TIMEOUT",
]