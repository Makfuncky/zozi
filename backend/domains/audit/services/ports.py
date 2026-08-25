"""Audit domain — sanctioned cross-domain READ surface (ports).

Per ARCHITECTURE_DIAGRAM.md Law 3, cross-domain reads may ONLY happen through a
publishing domain's ports.py. Other domains import these functions instead of
importing domains.audit.models or domains.audit.services directly.

These are pure read helpers: no writes, no business decisions, no permission
checks (callers remain responsible for feature gating via rbac).
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import select

from .events import AuditEvent  # noqa: F401 — re-export for type hints


def _get_models():
    from domains.audit.models.audit_schema_models import AuditLog, CommandCenterView
    return AuditLog, CommandCenterView


def get_audit_log_by_id(db, id_: int):
    """Return AuditLog by primary key (or None)."""
    AuditLog, _ = _get_models()
    return db.get(AuditLog, id_)


def list_audit_logs(db, limit: int = 100) -> list:
    """Return up to ``limit`` AuditLog rows, most-recent first."""
    AuditLog, _ = _get_models()
    stmt = (
        select(AuditLog)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
    )
    return db.execute(stmt).scalars().all()


def list_audit_logs_by_entity(db, entity_type: str, entity_id: int) -> list:
    """Return all audit logs for a specific entity."""
    AuditLog, _ = _get_models()
    stmt = (
        select(AuditLog)
        .where(AuditLog.entity_type == entity_type, AuditLog.entity_id == entity_id)
        .order_by(AuditLog.created_at.desc())
    )
    return db.execute(stmt).scalars().all()


def list_audit_logs_by_user(db, user_id: int, limit: int = 100) -> list:
    """Return audit logs for a specific user."""
    AuditLog, _ = _get_models()
    stmt = (
        select(AuditLog)
        .where(AuditLog.user_id == user_id)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
    )
    return db.execute(stmt).scalars().all()


def get_command_center_view_by_id(db, id_: int):
    """Return CommandCenterView by primary key (or None)."""
    _, CommandCenterView = _get_models()
    return db.get(CommandCenterView, id_)


def list_command_center_views_by_user(db, user_id: int) -> list:
    """Return all CommandCenterView rows for a user."""
    _, CommandCenterView = _get_models()
    stmt = select(CommandCenterView).where(CommandCenterView.user_id == user_id)
    return db.execute(stmt).scalars().all()


__all__ = [
    "get_audit_log_by_id",
    "list_audit_logs",
    "list_audit_logs_by_entity",
    "list_audit_logs_by_user",
    "get_command_center_view_by_id",
    "list_command_center_views_by_user",
]
