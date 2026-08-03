"""
Request IP extraction middleware - runs first to extract and store client IP.
"""
from __future__ import annotations

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from utils.ip_utils import set_request_ip
import logging

logger = logging.getLogger(__name__)


class IPExtractionMiddleware(BaseHTTPMiddleware):
    """
    Extracts client IP address from request and stores it in request.state.
    This must be the first middleware to ensure IP is available for all downstream middleware.
    """
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        set_request_ip(request)
        return await call_next(request)
