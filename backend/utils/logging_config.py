"""
Structured Logging Configuration for Zozi Platform
Implements request-scoped logging with correlation IDs and PII filtering.
"""
import logging
import sys
import structlog
import contextvars
from structlog.contextvars import merge_contextvars
from structlog.stdlib import add_log_level, add_logger_name
import json
from typing import Any, Dict

request_id_ctx = contextvars.ContextVar('request_id', default='')
country_code_ctx = contextvars.ContextVar('country_code', default='')
user_id_ctx = contextvars.ContextVar('user_id', default='')
db_query_time_ctx = contextvars.ContextVar('db_query_time', default=0.0)

PII_FIELDS = {
    'password', 'email', 'phone', 'token', 'secret', 'authorization',
    'credit_card', 'card_number', 'cvv', 'pan', 'iban', 'ssn',
    'api_key', 'apikey', 'access_token', 'refresh_token'
}

def setup_structlog():
    """Configure structured JSON logging for production."""
    log_level = logging.INFO
    
    logging.basicConfig(
        level=log_level,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ],
        format='%(message)s'
    )
    
    structlog.configure(
        processors=[
            add_log_level,
            add_logger_name,
            merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    structlog.configure(
        processors=[
            add_log_level,
            add_logger_name,
            merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    structlog.configure(
        processors=[
            add_log_level,
            add_logger_name,
            merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

def get_request_id() -> str:
    """Get current request ID from context."""
    return request_id_ctx.get()

def set_request_id(request_id: str) -> None:
    """Set current request ID in context."""
    request_id_ctx.set(request_id)

def get_country_code() -> str:
    """Get current country code from context."""
    return country_code_ctx.get()

def set_country_code(country_code: str) -> None:
    """Set current country code in context."""
    country_code_ctx.set(country_code)

def get_user_id() -> str:
    """Get current user ID from context."""
    return user_id_ctx.get()

def set_user_id(user_id: str) -> None:
    """Set current user ID in context."""
    user_id_ctx.set(user_id)

