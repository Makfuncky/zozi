"""audit domain - sanctioned cross-domain READ surface (ports).

Per NEW_STRUCTURE.md Law 3, cross-domain *reads* may ONLY happen through a
publishing domain's ``ports.py``. Other domains import these classes instead
of importing ``domains.audit.models`` directly.

A3 / RESOLVER Â§26 ACC-01 â€” re-export the audit-schema ORM classes the accounts
god-module hub used to own, so cross-domain readers resolve them via this
sanctioned ports surface (Law 3) instead of ``domains.governance.models``.
"""

from __future__ import annotations

from typing import Any

from domains.audit.models.audit_schema_models import AuditLog, CommandCenterView


# ── Sanctioned cross-domain service re-exports (Law 3 / module-routers use only) ─
# These are intentionally re-exported here so module routers import only from
# the publishing domain's ``ports.py`` (rather than reaching into
# ``domains.audit.services.logs.audit_service`` directly).

_LAZY_AUDIT_EXPORTS: dict[str, tuple[str, str]] = {
    "AuditAction": ("domains.audit.services.logs.audit_service", "AuditAction"),
    "audit_log": ("domains.audit.services.logs.audit_service", "audit_log"),
    "get_compliance_engine": ("domains.audit.services.compliance_engine", "get_compliance_engine"),
    "AuditService": ("domains.audit.services.audit_service", "AuditService"),
    "get_audit_logs": ("domains.audit.services.audit_service", "get_audit_logs"),
    "get_unique_actions": ("domains.audit.services.audit_service", "get_unique_actions"),
}


def __getattr__(name: str) -> Any:
    if name in _LAZY_AUDIT_EXPORTS:
        import importlib
        module_path, symbol = _LAZY_AUDIT_EXPORTS[name]
        mod = importlib.import_module(module_path)
        value = getattr(mod, symbol)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "AuditLog",
    "CommandCenterView",
    "AuditAction",
    "audit_log",
]

