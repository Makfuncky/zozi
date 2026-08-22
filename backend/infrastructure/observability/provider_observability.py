"""Observability Provider
======================
Centralises Sentry capture calls so services no longer import ``sentry_sdk``
directly. The Sentry SDK stays an optional dependency — when it is not installed
the capture helpers become no-ops.

Real implementation relocated from ``providers.observability`` (P13 root-leak
cleanup). ``providers/observability.py`` is now a backward-compatible re-export
shim.
"""
from __future__ import annotations

import importlib
from typing import Any, Optional


def capture_exception(exc: BaseException) -> None:
    """Capture an exception to Sentry (no-op when sentry_sdk is unavailable)."""
    try:
        sentry_sdk = importlib.import_module("sentry_sdk")
        sentry_sdk.capture_exception(exc)
    except Exception:
        pass


def capture_message(message: str, level: str = "info", **kwargs: Any) -> None:
    """Capture a message to Sentry (no-op when sentry_sdk is unavailable)."""
    try:
        sentry_sdk = importlib.import_module("sentry_sdk")
        sentry_sdk.capture_message(message, level=level, **kwargs)
    except Exception:
        pass


__all__ = ["capture_exception", "capture_message"]
