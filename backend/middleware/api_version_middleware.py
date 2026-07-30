"""API Version Header Middleware

Adds API version support via HTTP header for backward compatibility.
Supports both URL (/api/v1/...) and header (API-Version: v1) approaches.
"""
from __future__ import annotations

import logging
import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

class ApiVersionMiddleware(BaseHTTPMiddleware):
    """Middleware that extracts API version from headers and stores it in request state."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Extract API version from header (e.g., 'API-Version: v1')
        api_version_header = request.headers.get('API-Version', '')

        # Parse version - support 'v1', 'v2', etc.
        request.state.api_version = api_version_header.lower() if api_version_header.startswith('v') else 'v1'

        # Log version for observability
        request_id = str(uuid.uuid4())[:8]
        path = request.url.path
        version = request.state.api_version
        logger.info(
            "API version detected: %s | Request: %s | ID: %s",
            version, path, request_id
        )

        response = await call_next(request)

        # Add version header to response for client info
        response.headers['X-API-Version'] = request.state.api_version

        return response
