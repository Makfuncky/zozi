"""Audit domain — public facade.

Exports the public API for the audit domain. Uses lazy imports to avoid
circular dependency issues at module load time.
"""
from __future__ import annotations

from typing import Any

_LAZY_EXPORTS: dict[str, tuple[str, str]] = {
    # services
    "AuditService": ("domains.audit.services.audit_service", "AuditService"),
    "AuditTrailService": ("domains.audit.services.logs.audit_trail_service", "AuditTrailService"),
    "AuditQueryService": ("domains.audit.services.logs.audit_query_service", "AuditQueryService"),
    "ComplianceService": ("domains.audit.services.compliance_service", "ComplianceService"),
    "ComplianceEngine": ("domains.audit.services.compliance_engine", "ComplianceEngine"),
    "DataResidencyService": ("domains.audit.services.data_residency_service", "DataResidencyService"),
    "RetentionService": ("domains.audit.services.retention_service", "RetentionService"),
    "SecurityAudit": ("domains.audit.services.security_audit", "SecurityAudit"),
    # models
    "AuditLog": ("domains.audit.models.audit_schema_models", "AuditLog"),
    "AuditSchema": ("domains.audit.models.audit_schema_models", "AuditSchema"),
    # functions
    "log_audit_event": ("domains.audit.services.logs.audit_service", "log_audit_event"),
}


def __getattr__(name: str) -> Any:
    module_path, attr_name = _LAZY_EXPORTS.get(name, (None, None))
    if module_path is None:
        raise AttributeError(f"module 'domains.audit' has no attribute {name!r}")
    import importlib
    mod = importlib.import_module(module_path)
    return getattr(mod, attr_name)


__all__ = list(_LAZY_EXPORTS.keys())
