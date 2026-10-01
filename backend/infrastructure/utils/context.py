"""Request-scoped context utilities.

Lightweight contextvar-based helpers used across the payments stack for
correlation ids and structured error logging. Degrades gracefully when no
request context is active (Law 30).
"""
from __future__ import annotations

import contextvars
import logging
import uuid
from typing import Any, Optional

_request_info: contextvars.ContextVar[dict] = contextvars.ContextVar("zozi_request_info", default={})


class request_context:
    """Context manager that snapshots request metadata for the active task."""

    def __init__(self, **kwargs: Any) -> None:
        self._kwargs = kwargs
        self._token = None  # type: ignore[var-annotated]

    def __enter__(self) -> "request_context":
        current = dict(_request_info.get() or {})
        current.update(self._kwargs)
        if "correlation_id" not in current:
            current["correlation_id"] = uuid.uuid4().hex
        self._token = _request_info.set(current)
        return self

    def __exit__(self, *exc: Any) -> None:
        if self._token is not None:
            _request_info.reset(self._token)

    @classmethod
    def get(cls) -> dict:
        return _request_info.get() or {}


def get_correlation_id() -> Optional[str]:
    """Return the active correlation id (or None when outside a request)."""
    info = _request_info.get() or {}
    return info.get("correlation_id")


def log_service_error(logger: logging.Logger, message: str, **extra: Any) -> None:
    """Emit a structured error log line with the correlation id attached."""
    payload = {"correlation_id": get_correlation_id(), **extra}
    logger.error("%s %s", message, payload)
