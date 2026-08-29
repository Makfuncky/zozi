"""Backward-compat shim for security-audit helpers.

The canonical ``log_security_event`` implementation now lives in
``infrastructure.security.audit_log``. This shim keeps legacy import sites in
``middleware`` and elsewhere working without changes.
"""
from __future__ import annotations

from infrastructure.security.audit_log import (  # noqa: F401
    SECURITY_EVENTS,
    log_security_event,
)

__all__ = ["log_security_event", "SECURITY_EVENTS"]
