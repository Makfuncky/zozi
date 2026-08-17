"""Backward-compatible re-export shim for role-permission write operations.

Names are resolved lazily via module-level `__getattr__` so this shim never
contributes to an import-time cycle.
"""
from __future__ import annotations

import importlib
from typing import Any

_REEXPORTS: dict[str, tuple[str, str]] = {
    # No surviving canonical implementation. See the stub below.
}


def __getattr__(name: str) -> Any:
    if name in _REEXPORTS:
        module_path, attr = _REEXPORTS[name]
        return getattr(importlib.import_module(module_path), attr)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


from typing import Optional

from sqlalchemy.orm import Session

from models import RolePermissionSetting
from utils.audit import AuditAction, audit_log
import structlog
logger = structlog.get_logger(__name__)


def upsert_role_permission_setting(
    db: Session,
    *,
    role: str,
    permissions_json,
    country_code: Optional[str] = None,
    created_by: Optional[int] = None,
    updated_by: Optional[int] = None,
    **kw,
) -> RolePermissionSetting:
    """Insert or update the permission set for a (role, country_code) pair.

    ``updated_by`` is accepted as an alias for ``updated_by_id`` used by legacy
    callers; ``created_by`` seeds the creator on first insert.
    """
    actor = updated_by if updated_by is not None else kw.get("updated_by_id")
    existing = (
        db.query(RolePermissionSetting)
        .filter(
            RolePermissionSetting.role == role,
            RolePermissionSetting.country_code == country_code,
        )
        .first()
    )
    if existing is not None:
        existing.permissions_json = permissions_json
        if actor is not None:
            existing.updated_by = actor
        db.commit()
        db.refresh(existing)
        record = existing
    else:
        record = RolePermissionSetting(
            role=role,
            permissions_json=permissions_json,
            country_code=country_code,
            created_by=created_by if created_by is not None else actor,
            updated_by=actor,
        )
        db.add(record)
        db.commit()
        db.refresh(record)

    try:
        audit_log(
            db=db,
            actor_id=actor,
            action=AuditAction.PERMISSION_GRANT,
            entity="role_permission_settings",
            entity_key=str(record.id),
            details={"role": role, "country_code": country_code},
        )
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as e:
        # Best-effort audit; the setting write already committed.
        logger.exception("upsert_role_permission_setting_failed", error=str(e))

    return record