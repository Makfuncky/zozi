"""Service-level observability helpers.

Provides structured logging with correlation IDs and metrics counters
for critical domain services.
"""
from __future__ import annotations

import logging
import time
import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from functools import wraps
from typing import Any, Callable, Generator, Optional

from infrastructure.observability.logging_config import (
    request_id_ctx,
    user_id_ctx,
    country_code_ctx,
)
from infrastructure.observability.metrics import (
    db_query_duration_seconds,
    db_connections,
)

logger = logging.getLogger(__name__)

service_request_count: ContextVar[dict[str, int]] = ContextVar(
    "service_request_count", default={}
)
service_error_count: ContextVar[dict[str, int]] = ContextVar(
    "service_error_count", default={}
)


def generate_correlation_id() -> str:
    """Generate a new correlation ID for request tracing."""
    return str(uuid.uuid4())


def set_correlation_id(correlation_id: str) -> None:
    """Set the correlation ID in the current context."""
    request_id_ctx.set(correlation_id)


def get_correlation_id() -> str:
    """Get the current correlation ID from context."""
    return request_id_ctx.get()


def set_context_user(user_id: Optional[str] = None, country_code: Optional[str] = None) -> None:
    """Set user context for structured logging."""
    if user_id:
        user_id_ctx.set(str(user_id))
    if country_code:
        country_code_ctx.set(country_code)


def clear_context() -> None:
    """Clear all context variables."""
    request_id_ctx.set("")
    user_id_ctx.set("")
    country_code_ctx.set("")


@contextmanager
def request_context(
    correlation_id: Optional[str] = None,
    user_id: Optional[str] = None,
    country_code: Optional[str] = None,
) -> Generator[None, None, None]:
    """Context manager that sets correlation ID and user context for a request.

    Usage:
        with request_context(correlation_id="abc-123", user_id="42"):
            result = do_work()
    """
    cid = correlation_id or generate_correlation_id()
    set_correlation_id(cid)
    if user_id:
        user_id_ctx.set(str(user_id))
    if country_code:
        country_code_ctx.set(country_code)
    try:
        yield
    finally:
        clear_context()


def log_service_call(
    service_name: str,
    method_name: str,
    *,
    level: str = "info",
    **extra: Any,
) -> None:
    """Log a service method call with structured context."""
    log_data = {
        "service": service_name,
        "method": method_name,
        "correlation_id": get_correlation_id(),
        **extra,
    }
    getattr(logger, level)(f"service_call.{service_name}.{method_name}", **log_data)


def log_service_error(
    service_name: str,
    method_name: str,
    error: Exception,
    **extra: Any,
) -> None:
    """Log a service error with structured context."""
    log_data = {
        "service": service_name,
        "method": method_name,
        "error_type": type(error).__name__,
        "error_message": str(error),
        "correlation_id": get_correlation_id(),
        **extra,
    }
    logger.error(
        f"service_error.{service_name}.{method_name}",
        **log_data,
    )


def track_db_query(query_type: str, duration_seconds: float) -> None:
    """Track database query duration for observability."""
    try:
        db_query_duration_seconds.labels(query_type=query_type).observe(duration_seconds)
    except Exception:
        pass


@contextmanager
def db_query_timer(query_type: str) -> Generator[None, None, None]:
    """Context manager that times a database query and records to Prometheus.

    Usage:
        with db_query_timer("select_user"):
            user = db.query(User).filter(User.id == user_id).first()
    """
    start = time.perf_counter()
    try:
        yield
    finally:
        track_db_query(query_type, time.perf_counter() - start)


def instrument_service(service_name: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator that instruments a service method with logging and error tracking.

    Usage:
        @instrument_service("payments")
        def create_payment_intent(...):
            ...
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        method_name = getattr(func, "__qualname__", getattr(func, "__name__", "unknown"))

        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                log_service_call(service_name, method_name)
                start = time.perf_counter()
                try:
                    result = await func(*args, **kwargs)
                    duration = time.perf_counter() - start
                    log_service_call(
                        service_name, method_name,
                        level="debug",
                        duration_seconds=round(duration, 4),
                        status="success",
                    )
                    return result
                except Exception as e:
                    duration = time.perf_counter() - start
                    log_service_error(
                        service_name, method_name, e,
                        duration_seconds=round(duration, 4),
                    )
                    raise

            return async_wrapper

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            log_service_call(service_name, method_name)
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                duration = time.perf_counter() - start
                log_service_call(
                    service_name, method_name,
                    level="debug",
                    duration_seconds=round(duration, 4),
                    status="success",
                )
                return result
            except Exception as e:
                duration = time.perf_counter() - start
                log_service_error(
                    service_name, method_name, e,
                    duration_seconds=round(duration, 4),
                )
                raise

        return sync_wrapper

    return decorator


import asyncio  # noqa: E402 - placed at bottom to avoid circular import in type checkers
