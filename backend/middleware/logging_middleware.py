from __future__ import annotations

import time
from typing import Awaitable, Callable

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from utils.logging_config import country_code_ctx, request_id_ctx, user_id_ctx, db_query_time_ctx
from utils.metrics import db_query_duration_seconds, http_request_duration_seconds, http_requests_total


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        request_id = request_id_ctx.get() or request.headers.get("X-Request-ID", "")
        if request_id:
            request_id_ctx.set(request_id)
            request.state.request_id = request_id

        user_id = getattr(request.state, "user_id", None)
        if user_id:
            user_id_ctx.set(str(user_id))

        country_code = getattr(request.state, "country_code", None)
        if country_code:
            country_code_ctx.set(country_code)

        start_time = time.monotonic()
        response: Response | None = None
        error_occurred = False
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            error_occurred = True
            raise
        finally:
            duration_ms = round((time.monotonic() - start_time) * 1000, 2)
            status_code = response.status_code if response is not None else 500
            method = request.method
            path = str(request.url.path)

            http_request_duration_seconds.labels(method=method, endpoint=path).observe(duration_ms / 1000)
            http_requests_total.labels(method=method, endpoint=path, status=str(status_code)).inc()

            log = structlog.get_logger("zozi.request")
            if error_occurred or status_code >= 400:
                log.error(
                    "request_failed",
                    method=method,
                    path=path,
                    status_code=status_code,
                    duration_ms=duration_ms,
                    error=error_occurred,
                )
            else:
                log.info(
                    "request_complete",
                    method=method,
                    path=path,
                    status_code=status_code,
                    duration_ms=duration_ms,
                )
            if response is not None:
                response.headers["X-Request-ID"] = request_id
            db_query_time_ctx.set(0.0)

