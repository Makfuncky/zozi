"""Backward-compatible re-export shim for employee write operations.

This module intentionally performs NO imports at module-load time. It used to
re-export handler functions from `controllers.hr.employees_controller`, which
created an import-time circular-import cycle (`employees_controller` ->
`employee_write_service` -> `employees_controller`). Resolving names lazily via
module-level `__getattr__` breaks that cycle: the underlying controller module
is only imported on first attribute access, by which point the importing module
is fully initialised.
"""
from __future__ import annotations

import importlib
from typing import Any

_REEXPORTS: dict[str, tuple[str, str]] = {
    "approve_work_log": ("controllers.hr.employees_controller", "approve_work_log"),
    "create_employee": ("controllers.hr.employees_controller", "create_employee"),
    "create_employee_document": ("controllers.hr.employees_controller", "create_employee_document"),
    "create_employee_relation": ("controllers.hr.employees_controller", "create_employee_relation"),
    "create_employee_role": ("controllers.hr.employees_controller", "create_employee_role"),
    "create_leave_request": ("controllers.hr.employees_controller", "create_leave_request"),
    "create_office": ("controllers.hr.employees_controller", "create_office"),
    "delete_employee": ("controllers.hr.employees_controller", "delete_employee"),
    "delete_office": ("controllers.hr.employees_controller", "delete_office"),
    "update_employee": ("controllers.hr.employees_controller", "update_employee"),
    "update_office": ("controllers.hr.employees_controller", "update_office"),
    "create_shift_roster": ("services.hr.shift_roster_service", "create_shift_roster"),
}


def __getattr__(name: str) -> Any:
    if name in _REEXPORTS:
        module_path, attr = _REEXPORTS[name]
        return getattr(importlib.import_module(module_path), attr)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


from typing import Optional, Union

from datetime import datetime

from sqlalchemy.orm import Session

from utils.datetime_utils import utcnow as _utcnow
from utils.soft_delete import soft_delete
from models import (
    EmployeeAttendance,
    EmployeeWorkLog,
    EmployeeDocument,
    EmployeeRelation,
    DynamicQRSession,
    RevokedToken,
)
import structlog
logger = structlog.get_logger(__name__)


def _is_orm(obj, Model) -> bool:
    return isinstance(obj, Model)


def _apply_changes(record, changes):
    for field, value in (changes or {}).items():
        if value is None:
            continue
        if hasattr(record, field):
            setattr(record, field, value)
    return record


def create_employee_attendance(
    db: Session,
    *,
    employee_id: int,
    date,
    **data,
) -> EmployeeAttendance:
    record = EmployeeAttendance(employee_id=employee_id, date=date, **data)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def update_employee_attendance(db: Session, record_or_id, changes: Optional[dict] = None, **kw):
    if _is_orm(record_or_id, EmployeeAttendance):
        record = record_or_id
    else:
        record = db.get(EmployeeAttendance, int(record_or_id))
        if record is None:
            raise ValueError(f"EmployeeAttendance {record_or_id} not found")
    _apply_changes(record, changes or kw)
    db.commit()
    db.refresh(record)
    return record


def create_employee_work_log(
    db: Session,
    *,
    employee_id: int,
    **data,
) -> EmployeeWorkLog:
    record = EmployeeWorkLog(employee_id=employee_id, **data)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def update_employee_document(db: Session, record_or_id, changes: Optional[dict] = None, **kw):
    if _is_orm(record_or_id, EmployeeDocument):
        record = record_or_id
    else:
        record = db.get(EmployeeDocument, int(record_or_id))
        if record is None:
            raise ValueError(f"EmployeeDocument {record_or_id} not found")
    _apply_changes(record, changes or kw)
    db.commit()
    db.refresh(record)
    return record


def delete_employee_relation(
    db: Session,
    relation_or_id,
    acting_user: Optional[Union[dict, int]] = None,
    reason: Optional[str] = None,
):
    if _is_orm(relation_or_id, EmployeeRelation):
        record = relation_or_id
    else:
        record = db.get(EmployeeRelation, int(relation_or_id))
        if record is None:
            raise ValueError(f"EmployeeRelation {relation_or_id} not found")
    return soft_delete(db, EmployeeRelation, record.id, acting_user, reason=reason)


def create_dynamic_qr_session(
    db: Session,
    *,
    employee_id: int,
    qr_token: str,
    expires_at,
    **data,
) -> DynamicQRSession:
    record = DynamicQRSession(employee_id=employee_id, qr_token=qr_token, expires_at=expires_at, **data)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def update_dynamic_qr_session(db: Session, record_or_id, changes: Optional[dict] = None, **kw):
    if _is_orm(record_or_id, DynamicQRSession):
        record = record_or_id
    else:
        record = db.get(DynamicQRSession, int(record_or_id))
        if record is None:
            raise ValueError(f"DynamicQRSession {record_or_id} not found")
    _apply_changes(record, changes or kw)
    db.commit()
    db.refresh(record)
    return record


def update_qr_sessions_expiry(
    db: Session,
    sessions_list: Optional[list] = None,
    as_of: Optional[datetime] = None,
    **kw,
):
    """Expire dynamic QR sessions that are still valid as of ``as_of``.

    Accepts an explicit list of session objects (legacy controller form) and/or
    an ``as_of`` timestamp. Sessions whose ``expires_at`` is already in the past
    are left untouched.
    """
    if as_of is None:
        as_of = _utcnow()
    if sessions_list is None:
        sessions_list = (
            db.query(DynamicQRSession)
            .filter(
                DynamicQRSession.expires_at > as_of,
                DynamicQRSession.used_at.is_(None),
            )
            .all()
        )
    expired = 0
    for session in sessions_list:
        if getattr(session, "expires_at", None) is None or session.expires_at > as_of:
            session.expires_at = as_of
            expired += 1
    if expired:
        db.commit()
    return {"expired": expired}


def create_revoked_token(
    db: Session,
    *,
    jti: str,
    user_id: Optional[int] = None,
    expires_at: Optional[datetime] = None,
    **data,
) -> RevokedToken:
    record = RevokedToken(jti=jti, user_id=user_id, expires_at=expires_at, **data)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record
