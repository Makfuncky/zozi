"""Security services - audit service."""
from __future__ import annotations

from domains.audit.services.logs.audit_service import AuditService, AuditAction, audit_log
from domains.audit.services.logs.audit_query_service import get_audit_logs, get_unique_actions
from domains.audit.services.logs.user_activity_tracker import UserActivityTracker, get_user_activity_tracker

# Lazy imports to avoid circular dependency
import importlib

def get_audit_log_page(*args, **kwargs):
    """Lazy import to avoid circular dependency."""
    mod = importlib.import_module('domains.governance.services.settings.misc_service')
    return mod.get_audit_log_page(*args, **kwargs)

def get_available_audit_actions(*args, **kwargs):
    """Lazy import to avoid circular dependency."""
    mod = importlib.import_module('domains.governance.services.settings.misc_service')
    return mod.get_available_audit_actions(*args, **kwargs)

__all__ = [
    "AuditService",
    "AuditAction",
    "audit_log",
    "get_audit_logs",
    "get_unique_actions",
    "UserActivityTracker",
    "get_user_activity_tracker",
    "get_audit_log_page",
    "get_available_audit_actions",
]
