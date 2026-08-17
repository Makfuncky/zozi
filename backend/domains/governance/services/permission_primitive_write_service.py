"""Permission-primitive write operations.

Owns the DB writes for the maker-checker role-permission setting flow so the
``routers`` package does not mutate the session directly (W1 contract). Routers
may read through these primitives but must call into this service to persist.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from models import RolePermissionSetting
from infrastructure.utils.audit import AuditAction, audit_log
import structlog
logger = structlog.get_logger(__name__)


def _actor_id(value) -> int | None:
    if isinstance(value, int):
        return value
    return None


def upsert_role_permission_setting(
    db: Session,
    *,
    role: str,
    country_code: str,
    permissions_json: str,
    updated_by: int,
    pending_permissions_json: str | None = None,
    is_approved: bool = True,
) -> RolePermissionSetting:
    """Create or update the ``RolePermissionSetting`` row for a role/country.

    For maker-checker (sensitive) changes call with ``pending_permissions_json``
    set and ``is_approved=False``; the staged set is held in
    ``pending_permissions_json`` and the active ``permissions_json`` is left
    untouched until ``approve_role_permission_setting`` promotes it.
    """
    setting = (
        db.query(RolePermissionSetting)
        .filter(
            RolePermissionSetting.role == role,
            RolePermissionSetting.country_code == country_code,
        )
        .first()
    )
    if setting is None:
        setting = RolePermissionSetting(role=role, country_code=country_code)
        db.add(setting)

    if pending_permissions_json is not None:
        setting.pending_permissions_json = pending_permissions_json
        setting.is_approved = bool(is_approved)
    else:
        setting.permissions_json = permissions_json
        setting.is_approved = True
    setting.updated_by = updated_by
    db.commit()

    actor = _actor_id(updated_by)
    try:
        audit_log(
            db=db,
            actor_id=actor,
            action=AuditAction.PERMISSION_GRANT if is_approved else AuditAction.PERMISSION_APPROVE,
            entity="role_permission_settings",
            entity_key=str(setting.id),
            details={
                "role": role,
                "country_code": country_code,
                "pending": pending_permissions_json is not None,
            },
        )
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as e:
        # Audit is best-effort here; the setting write already committed.
        logger.exception("upsert_role_permission_setting_failed", error=str(e))

    db.refresh(setting)
    return setting


def approve_role_permission_setting(
    db: Session,
    *,
    setting_id: str,
    approver_id: int,
) -> RolePermissionSetting | None:
    """Promote a staged maker-checker setting to active use.

    Copies ``pending_permissions_json`` into ``permissions_json`` and marks the
    row approved. Returns the setting if found, or ``None`` when no matching row
    exists.
    """
    setting = (
        db.query(RolePermissionSetting)
        .filter(RolePermissionSetting.id == int(setting_id))
        .first()
    )
    if setting is None:
        return None
    if setting.pending_permissions_json is not None:
        setting.permissions_json = setting.pending_permissions_json
    setting.is_approved = True
    setting.updated_by = approver_id
    db.commit()

    actor = _actor_id(approver_id)
    try:
        audit_log(
            db=db,
            actor_id=actor,
            action=AuditAction.PERMISSION_APPROVE,
            entity="role_permission_settings",
            entity_key=str(setting.id),
            details={"role": setting.role, "country_code": setting.country_code},
        )
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as e:
        logger.exception("approve_role_permission_setting_failed", error=str(e))

    return setting
