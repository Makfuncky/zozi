"""
Request ID Middleware for Zozi Platform
Generates and manages request IDs for tracing and correlation.
"""
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp
import structlog
from utils.logging_config import request_id_ctx, set_request_id, get_request_id

logger = structlog.get_logger(__name__)

class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware that adds request IDs to all requests for tracing."""
    
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))
        set_request_id(request_id)
        request.state.request_id = request_id
        
        response = await call_next(request)
        response.headers['X-Request-ID'] = request_id
        return response

