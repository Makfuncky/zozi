"""Governance domain — public facade.

Exports the public API for the governance domain. Uses lazy imports to avoid
circular dependency issues at module load time.
"""
from __future__ import annotations

from typing import Any

_LAZY_EXPORTS: dict[str, tuple[str, str]] = {
    # services
    "AdminService": ("domains.governance.services.admin.admin_service", "AdminService"),
    "BulkOpsService": ("domains.governance.services.admin.bulk_ops_service", "BulkOpsService"),
    "ApprovalMatrixService": ("domains.governance.services.approval.approval_matrix_service", "ApprovalMatrixService"),
    "IncidentService": ("domains.governance.services.incident.incident_service", "IncidentService"),
    "CommandCenterService": ("domains.governance.services.command_center.command_center_service", "CommandCenterService"),
    "WorkflowEngine": ("domains.governance.services.workflow_engine", "WorkflowEngine"),
    "Operations": ("domains.governance.services.operations", "Operations"),
    "IAMServiceAccounts": ("domains.governance.services.auth.iam_service_accounts", "IAMServiceAccounts"),
    # models
    "AuditLog": ("domains.governance.models.core", "AuditLog"),
    "User": ("domains.accounts.models.user", "User"),
    "Fraud": ("domains.governance.models.fraud", "Fraud"),
    # functions
    "archive_entity": ("domains.governance.services.operations", "archive_entity"),
    "restore_entity": ("domains.governance.services.operations", "restore_entity"),
}


def __getattr__(name: str) -> Any:
    module_path, attr_name = _LAZY_EXPORTS.get(name, (None, None))
    if module_path is None:
        raise AttributeError(f"module 'domains.governance' has no attribute {name!r}")
    import importlib
    mod = importlib.import_module(module_path)
    return getattr(mod, attr_name)


__all__ = list(_LAZY_EXPORTS.keys())
