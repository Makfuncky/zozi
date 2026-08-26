"""Backward-compat shim — canonical location is domains/audit/services/logs/audit_service.py."""
# Lazy imports to avoid circular dependency
import importlib

def __getattr__(name):
    """Lazy import to avoid circular dependency."""
    if name in ('audit_log', 'AuditAction', 'AuditCategory', 'AuditSeverity', 'AuditService'):
        mod = importlib.import_module('domains.audit.services.logs.audit_service')
        return getattr(mod, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
