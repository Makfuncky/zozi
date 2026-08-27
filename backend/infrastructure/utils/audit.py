"""Backward-compat shim — canonical location is domains/audit/services/logs/audit_service.py.

Required because infrastructure/utils/* cannot import from domains/* (Law 1).
"""
import importlib


def __getattr__(name):
    if name in ("audit_log", "AuditAction", "AuditCategory", "AuditSeverity", "AuditService"):
        mod = importlib.import_module("domains.audit.services.logs.audit_service")
        return getattr(mod, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
