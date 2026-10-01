"""
Request ID Middleware for Zozi Platform
Generates and manages request IDs for tracing and correlation.
"""
import contextvars
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import structlog

logger = structlog.get_logger(__name__)

_request_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="")


def set_request_id(request_id: str) -> None:
    """Set the request ID in the current context."""
    _request_id_ctx.set(request_id)


def get_request_id() -> str:
    """Get the request ID from the current context."""
    return _request_id_ctx.get()


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware that adds request IDs to all requests for tracing."""
    
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))
        set_request_id(request_id)
        request.state.request_id = request_id
        
        response = await call_next(request)
        response.headers['X-Request-ID'] = request_id
        return response


