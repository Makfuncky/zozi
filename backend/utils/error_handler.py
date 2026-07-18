"""
Global Error Handling System for Zozi Platform
Provides centralized exception handling, Sentry integration, and structured error responses.
"""
import logging
import traceback
from typing import Any, Dict, Optional
from datetime import datetime
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import structlog

from utils.ip_utils import get_request_ip

logger = structlog.get_logger(__name__)

class ErrorHandler:
    """Centralized error handling with Sentry integration."""
    
    def __init__(self, sentry_dsn: Optional[str] = None):
        self.sentry_initialized = False
        if sentry_dsn:
            try:
                import sentry_sdk
                from sentry_sdk.integrations.fastapi import FastApiIntegration
                from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
                from sentry_sdk.integrations.redis import RedisIntegration
                
                sentry_sdk.init(
                    dsn=sentry_dsn,
                    integrations=[
                        FastApiIntegration(),
                        SqlalchemyIntegration(),
                        RedisIntegration(),
                    ],
                    traces_sample_rate=0.1,
                    environment="production",
                    before_send=self._before_send,
                )
                self.sentry_initialized = True
                logger.info("Sentry error tracking initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Sentry: {e}")
    
    def _before_send(self, event: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Filter and enrich Sentry events."""
        exc_info = hint.get("exc_info")
        if exc_info:
            exc_type, exc_value, tb = exc_info
            if exc_type and issubclass(exc_type, HTTPException):
                if exc_value.status_code < 500:
                    return None
        return event
    
    def capture_exception(self, exc: Exception, request: Optional[Request] = None, **kwargs):
        """Capture and log an exception."""
        import sentry_sdk
        
        error_context = {
            "error_type": type(exc).__name__,
            "error_message": str(exc),
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        if request:
            error_context["path"] = str(request.url.path)
            error_context["method"] = request.method
            error_context["client_ip"] = get_request_ip(request)
        
        logger.error("Application error", **error_context)
        
        if self.sentry_initialized:
            sentry_sdk.capture_exception(exc, **kwargs)
    
    def capture_message(self, message: str, level: str = "info", **kwargs):
        """Capture a message (non-exception) to Sentry."""
        import sentry_sdk
        
        if self.sentry_initialized:
            sentry_sdk.capture_message(message, level=level, **kwargs)


def create_error_handler(sentry_dsn: Optional[str] = None) -> ErrorHandler:
    """Create a global error handler instance."""
    return ErrorHandler(sentry_dsn)


async def global_exception_handler(request: Request, exc: Exception, error_handler: ErrorHandler):
    origin = request.headers.get("origin")
    headers = {}
    if origin:
        headers["Access-Control-Allow-Origin"] = origin
        headers["Access-Control-Allow-Credentials"] = "true"

    error_handler.capture_exception(exc, request)

    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=headers,
        )

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "request_id": getattr(request.state, 'request_id', 'unknown')
        },
        headers=headers,
    )


class AppError(Exception):
    """Custom application error with structured details."""
    
    def __init__(
        self,
        message: str,
        error_code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


def handle_app_error(exc: AppError) -> JSONResponse:
    """Handle custom AppError exceptions."""
    logger.error(
        "Application error",
        error_code=exc.error_code,
        message=exc.message,
        details=exc.details
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error_code,
            "message": exc.message,
            "details": exc.details
        }
    )

