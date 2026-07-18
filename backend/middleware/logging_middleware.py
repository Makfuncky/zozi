from __future__ import annotations

import time
from typing import Awaitable, Callable

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from utils.logging_config import country_code_ctx, request_id_ctx, user_id_ctx


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        request_id = request.headers.get("X-Request-ID", "")
        request_id_ctx.set(request_id)
        request.state.request_id = request_id

        user_id = getattr(request.state, "user_id", None)
        if user_id:
            user_id_ctx.set(str(user_id))

        country_code = getattr(request.state, "country_code", None)
        if country_code:
            country_code_ctx.set(country_code)

        response = await call_next(request)

        response.headers["X-Request-ID"] = request_id
        return response

