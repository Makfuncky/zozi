"""Logging configuration for Zozi Platform."""
import logging
import structlog
from contextvars import ContextVar

# Context variables for request tracking
request_id_ctx = ContextVar("request_id", default=None)
country_code_ctx = ContextVar("country_code", default=None)
user_id_ctx = ContextVar("user_id", default=None)
db_query_time_ctx = ContextVar("db_query_time", default=None)


def setup_structlog(log_level=logging.INFO):
    """Configure structured logging."""
    import logging
    logging.basicConfig(level=log_level)
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ]
    )


def get_request_id():
    """Get current request ID from context."""
    return request_id_ctx.get()


def set_request_id(request_id: str):
    """Set request ID in context."""
    request_id_ctx.set(request_id)
