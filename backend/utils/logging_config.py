from typing import Set
"""
Structured Logging Configuration for Zozi Platform
Implements request-scoped logging with correlation IDs, PII filtering,
file logging with rotation, and structured JSON output.
"""
import logging
import os
import re
import sys
import structlog
import contextvars
from structlog.contextvars import merge_contextvars
from structlog.stdlib import add_log_level, add_logger_name
from typing import Any, Dict, Optional
from logging.handlers import RotatingFileHandler

request_id_ctx = contextvars.ContextVar('request_id', default='')
country_code_ctx = contextvars.ContextVar('country_code', default='')
user_id_ctx = contextvars.ContextVar('user_id', default='')
db_query_time_ctx = contextvars.ContextVar('db_query_time', default=0.0)
session_id_ctx = contextvars.ContextVar('session_id', default='')

PII_FIELDS = {
    'password', 'email', 'phone', 'token', 'secret', 'authorization',
    'credit_card', 'card_number', 'cvv', 'pan', 'iban', 'ssn',
    'api_key', 'apikey', 'access_token', 'refresh_token',
    'cookie', 'set_cookie', 'x-csrf-token', 'x-api-key',
}

PII_PATTERNS = [
    (re.compile(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'), '****-****-****-XXXX'),
    (re.compile(r'\b\d{13,19}\b'), '****'),
    (re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'), '***@***.***'),
    (re.compile(r'\b\d{3}[-\s]?\d{3}[-\s]?\d{4}\b'), '***-***-****'),
]


def _scrub_pii_value(value: str) -> str:
    """Apply regex-based PII pattern scrubbing to a string value."""
    if not isinstance(value, str):
        return value
    for pattern, replacement in PII_PATTERNS:
        value = pattern.sub(replacement, value)
    return value


def _scrub_pii(logger: logging.Logger, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Scrub sensitive fields from log output before serialization."""
    scrubbed = {}
    for key, value in event_dict.items():
        if key.lower() in PII_FIELDS:
            scrubbed[key] = '[REDACTED]'
        elif isinstance(value, str):
            scrubbed[key] = _scrub_pii_value(value)
        elif isinstance(value, dict):
            scrubbed[key] = _scrub_dict(value)
        elif isinstance(value, list):
            scrubbed[key] = _scrub_list(value)
        else:
            scrubbed[key] = value
    return scrubbed


def _scrub_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively scrub PII from nested dictionaries."""
    result = {}
    for key, value in d.items():
        if key.lower() in PII_FIELDS:
            result[key] = '[REDACTED]'
        elif isinstance(value, dict):
            result[key] = _scrub_dict(value)
        elif isinstance(value, list):
            result[key] = _scrub_list(value)
        elif isinstance(value, str):
            result[key] = _scrub_pii_value(value)
        else:
            result[key] = value
    return result


def _scrub_list(lst: list) -> list:
    """Recursively scrub PII from lists."""
    result = []
    for item in lst:
        if isinstance(item, dict):
            result.append(_scrub_dict(item))
        elif isinstance(item, str):
            result.append(_scrub_pii_value(item))
        else:
            result.append(item)
    return result


def _add_context(logger: logging.Logger, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Enrich log entries with request context."""
    request_id = request_id_ctx.get()
    user_id = user_id_ctx.get()
    country_code = country_code_ctx.get()
    db_time = db_query_time_ctx.get()
    session_id = session_id_ctx.get()

    if request_id:
        event_dict['request_id'] = request_id
    if user_id:
        event_dict['user_id'] = user_id
    if country_code:
        event_dict['country_code'] = country_code
    if db_time:
        event_dict['db_query_time_ms'] = round(db_time, 2)
    if session_id:
        event_dict['session_id'] = session_id

    return event_dict


def _get_log_level(log_level: int) -> int:
    """Resolve log level, respecting environment overrides."""
    env_level = os.environ.get('LOG_LEVEL', '').upper()
    if env_level and hasattr(logging, env_level):
        return getattr(logging, env_level)
    return log_level


def setup_structlog(log_level: int = logging.INFO, log_file: Optional[str] = None):
    """Configure structured JSON logging with PII scrubbing, context enrichment, and file output."""
    resolved_level = _get_log_level(log_level)

    handlers = [logging.StreamHandler(sys.stdout)]

    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding='utf-8',
        )
        file_handler.setLevel(resolved_level)
        handlers.append(file_handler)

    logging.basicConfig(
        level=resolved_level,
        handlers=handlers,
        format='%(message)s',
        force=True,
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
            _scrub_pii,
            _add_context,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(resolved_level),
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


def get_session_id() -> str:
    """Get current session ID from context."""
    return session_id_ctx.get()


def set_session_id(session_id: str) -> None:
    """Set current session ID in context."""
    session_id_ctx.set(session_id)

