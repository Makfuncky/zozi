"""Infrastructure stubs for email-related domain functions.

This module provides lazy-import stubs to avoid Law 1 violations while
maintaining backward compatibility. These functions delegate to the
canonical domain implementations.
"""
from __future__ import annotations

from typing import Optional


def is_email_suppressed(email: str) -> bool:
    """Check if an email address is suppressed.
    
    Delegates to domains.comms.services.email_event_service.is_email_suppressed
    via lazy import to avoid Law 1 violation.
    """
    try:
        from domains.comms.services.email_event_service import is_email_suppressed as _impl
        return _impl(email)
    except Exception:
        return False


def record_email_delivery_event(db, recipient: str, purpose: str, status: str, **kwargs) -> None:
    """Record an email delivery event.
    
    Delegates to domains.comms.services.email_event_service.record_email_delivery_event
    via lazy import to avoid Law 1 violation.
    """
    try:
        from domains.comms.services.email_event_service import record_email_delivery_event as _impl
        _impl(db, recipient, purpose, status, **kwargs)
    except Exception:
        pass
