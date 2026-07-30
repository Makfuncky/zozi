"""
Global Error Handling System for Zozi Platform
Provides centralized exception handling, Sentry integration, and structured error responses.

Standardized Error Response Format (RFC 7807 Problem Details):
{
    "type": "https://zozi.com/errors/error-code",
    "title": "Short human-readable title",
    "status": 400,
    "detail": "Detailed error message",
    "instance": "/api/resource",
    "request_id": "abc-123",
    "timestamp": "2026-07-26T12:00:00Z",
    "errors": { ... }
}
"""
import logging
import traceback
from typing import Any, Dict, Optional
from datetime import datetime, timezone
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import structlog

from utils.ip_utils import get_request_ip
from utils.logging_config import get_request_id, get_user_id, get_country_code

logger = structlog.get_logger(__name__)


class ErrorCategory:
    AUTHENTICATION = "authentication_error"
    AUTHORIZATION = "authorization_error"
    VALIDATION = "validation_error"
    NOT_FOUND = "not_found_error"
    RATE_LIMIT = "rate_limit_error"
    DATABASE = "database_error"
    EXTERNAL_SERVICE = "external_service_error"
    BUSINESS_LOGIC = "business_logic_error"
    INTERNAL = "internal_error"


class ErrorHandler:
    """Centralized error handling with Sentry integration and structured logging."""

    def __init__(self, sentry_dsn: Optional[str] = None, environment: str = "development"):
        self.sentry_initialized = False
        self.sentry_dsn = sentry_dsn
        self.environment = environment
        if sentry_dsn:
            self._init_sentry()

    def _init_sentry(self):
        try:
            import sentry_sdk
            from sentry_sdk.integrations.fastapi import FastApiIntegration
            from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
            from sentry_sdk.integrations.redis import RedisIntegration

            sentry_sdk.init(
                dsn=self.sentry_dsn,
                integrations=[
                    FastApiIntegration(),
                    SqlalchemyIntegration(),
                    RedisIntegration(),
                ],
                traces_sample_rate=0.1,
                environment=self.environment,
                before_send=self._before_send,
                attach_stacktrace=True,
                send_default_pii=False,
            )
            self.sentry_initialized = True
            logger.info("sentry_initialized", dsn_configured=True, environment=self.environment)
        except ImportError:
            logger.warning("sentry_package_not_installed")
        except Exception as e:
            logger.error("sentry_init_failed", error=str(e))

    def _before_send(self, event: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Filter and enrich Sentry events before sending."""
        exc_info = hint.get("exc_info")
        if exc_info:
            exc_type, exc_value, tb = exc_info
            if exc_type and issubclass(exc_type, HTTPException):
                if exc_value.status_code < 500:
                    return None
            if exc_type and issubclass(exc_type, Exception):
                error_context = hint.get("context", {})
                request_id = error_context.get("request_id")
                if request_id:
                    event.setdefault("tags", {})["request_id"] = request_id
                user_id = error_context.get("user_id")
                if user_id:
                    event.setdefault("user", {})["id"] = str(user_id)
                country_code = error_context.get("country_code")
                if country_code:
                    event.setdefault("tags", {})["country_code"] = country_code
        return event

    def is_healthy(self) -> bool:
        return self.sentry_initialized

    def capture_exception(self, exc: Exception, request: Optional[Request] = None, category: str = ErrorCategory.INTERNAL, **kwargs):
        """Capture and log an exception with full context."""
        if not self.sentry_initialized:
            return

        try:
            import sentry_sdk
        except ImportError:
            return

        error_context = {
            "error_type": type(exc).__name__,
            "error_message": str(exc),
            "error_category": category,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        if request:
            error_context["path"] = str(request.url.path)
            error_context["method"] = request.method
            error_context["client_ip"] = get_request_ip(request)

        request_id = get_request_id()
        if request_id:
            error_context["request_id"] = request_id

        user_id = get_user_id()
        if user_id:
            error_context["user_id"] = user_id

        country_code = get_country_code()
        if country_code:
            error_context["country_code"] = country_code

        logger.error("application_error", **error_context)

        if self.sentry_initialized:
            with sentry_sdk.configure_scope() as scope:
                if request_id:
                    scope.set_tag("request_id", request_id)
                if user_id:
                    scope.set_user({"id": str(user_id)})
                if country_code:
                    scope.set_tag("country_code", country_code)
                scope.set_tag("error_category", category)
                scope.set_context("request", {
                    "path": str(request.url.path) if request else "",
                    "method": request.method if request else "",
                    "client_ip": get_request_ip(request) if request else "",
                })
                sentry_sdk.capture_exception(exc, **kwargs)

    def capture_message(self, message: str, level: str = "info", **kwargs):
        """Capture a message (non-exception) to Sentry."""
        import sentry_sdk

        if self.sentry_initialized:
            sentry_sdk.capture_message(message, level=level, **kwargs)

    def classify_error(self, exc: Exception, request: Optional[Request] = None) -> str:
        """Classify an error into a category for better tracking."""
        if isinstance(exc, HTTPException):
            if exc.status_code == 401:
                return ErrorCategory.AUTHENTICATION
            if exc.status_code == 403:
                return ErrorCategory.AUTHORIZATION
            if exc.status_code == 404:
                return ErrorCategory.NOT_FOUND
            if exc.status_code == 429:
                return ErrorCategory.RATE_LIMIT
            if exc.status_code < 500:
                return ErrorCategory.VALIDATION
            return ErrorCategory.INTERNAL
        if "database" in str(type(exc)).lower() or "sql" in str(type(exc)).lower():
            return ErrorCategory.DATABASE
        if "timeout" in str(exc).lower() or "connection" in str(exc).lower():
            return ErrorCategory.EXTERNAL_SERVICE
        return ErrorCategory.INTERNAL


def create_error_handler(sentry_dsn: Optional[str] = None, environment: str = "development") -> ErrorHandler:
    """Create a global error handler instance."""
    return ErrorHandler(sentry_dsn, environment)


def _build_problem_response(
    status: int,
    title: str,
    detail: str,
    error_type: Optional[str] = None,
    instance: Optional[str] = None,
    request_id: Optional[str] = None,
    errors: Optional[Dict[str, Any]] = None,
    category: Optional[str] = None,
) -> Dict[str, Any]:
    """Build RFC 7807 Problem Details response."""
    problem = {
        "type": error_type or f"https://zozi.com/errors/{status}",
        "title": title,
        "status": status,
        "detail": detail,
        "instance": instance or "",
        "request_id": request_id or "",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if category:
        problem["error_category"] = category
    if errors:
        problem["errors"] = errors
    return problem


def _get_cors_headers(request: Request) -> Dict[str, str]:
    headers = {}
    origin = request.headers.get("origin")
    if origin:
        headers["Access-Control-Allow-Origin"] = origin
        headers["Access-Control-Allow-Credentials"] = "true"
    return headers


async def global_exception_handler(request: Request, exc: Exception, error_handler: ErrorHandler):
    headers = _get_cors_headers(request)
    request_id = get_request_id() or getattr(request.state, 'request_id', '')
    user_id = get_user_id()
    country_code = get_country_code()

    if isinstance(exc, HTTPException):
        category = error_handler.classify_error(exc, request)
        error_handler.capture_exception(exc, request, category=category)
        body = _build_problem_response(
            status=exc.status_code,
            title="Request Error",
            detail=exc.detail,
            error_type=f"https://zozi.com/errors/http-{exc.status_code}",
            instance=str(request.url.path),
            request_id=request_id,
            category=category,
        )
        return JSONResponse(status_code=exc.status_code, content=body, headers=headers)

    if isinstance(exc, AppError):
        category = error_handler.classify_error(exc, request)
        error_handler.capture_exception(exc, request, category=category)
        body = _build_problem_response(
            status=exc.status_code,
            title=exc.error_code.replace("_", " ").title(),
            detail=exc.message,
            error_type=f"https://zozi.com/errors/{exc.error_code}",
            instance=str(request.url.path),
            request_id=request_id,
            errors=exc.details if exc.details else None,
            category=category,
        )
        return JSONResponse(status_code=exc.status_code, content=body, headers=headers)

    # Unhandled exceptions — log full traceback, return generic 500
    category = error_handler.classify_error(exc, request)
    error_handler.capture_exception(exc, request, category=category)
    logger.exception("unhandled_exception", path=str(request.url.path), request_id=request_id, user_id=user_id, country_code=country_code)

    body = _build_problem_response(
        status=500,
        title="Internal Server Error",
        detail="An unexpected error occurred",
        error_type="https://zozi.com/errors/internal-server-error",
        instance=str(request.url.path),
        request_id=request_id,
        category=category,
    )
    return JSONResponse(status_code=500, content=body, headers=headers)


class AppError(Exception):
    """Custom application error with structured details."""

    def __init__(
        self,
        message: str,
        error_code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
        category: str = ErrorCategory.INTERNAL,
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        self.category = category
        super().__init__(message)