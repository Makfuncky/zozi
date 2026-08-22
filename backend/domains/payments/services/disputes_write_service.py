"""Backward-compatible re-export shim for supplier dispute write operations.

This module intentionally performs NO imports at module-load time. It used to
re-export handler functions from `domains.payments.services.disputes_controller`, which
created an import-time circular-import cycle (`disputes_controller` ->
`disputes_write_service` -> `disputes_controller`). Resolving names lazily via
module-level `__getattr__` breaks that cycle: the underlying controller module
is only imported on first attribute access, by which point the importing module
is fully initialised.
"""
from __future__ import annotations

import importlib
from typing import Any

_REEXPORTS: dict[str, tuple[str, str]] = {
    "create_supplier_dispute": ("domains.payments.services.disputes_controller", "create_supplier_dispute"),
}


def __getattr__(name: str) -> Any:
    if name in _REEXPORTS:
        module_path, attr = _REEXPORTS[name]
        return getattr(importlib.import_module(module_path), attr)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


from typing import Optional

from sqlalchemy.orm import Session

from domains.comms.ports import Notification
from domains.comms.ports import SupplierNotificationPreference
from domains.governance.ports import SupplierDispute
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


def _resolve_user_id(supplier_id=None, dispute=None, user_id=None):
    if user_id is not None:
        return user_id
    if supplier_id is not None:
        return supplier_id
    if dispute is not None:
        return getattr(dispute, "supplier_id", None)
    return None


def create_dispute_notification(
    db: Session,
    *,
    user_id: Optional[int] = None,
    supplier_id: Optional[int] = None,
    dispute=None,
    country_code: str = "OM",
    type: Optional[str] = None,
    title: str = "",
    message: str = "",
    link: Optional[str] = None,
    is_read: bool = False,
    **kw,
) -> Notification:
    """Create a notification for a supplier dispute event.

    Compatible with the legacy controller form which passes ``user_id``,
    ``type``, ``title``, ``message``, ``link`` and ``is_read`` directly.
    """
    record = Notification(
        user_id=_resolve_user_id(supplier_id, dispute, user_id),
        title=title,
        message=message,
        link=link,
        type=type,
        is_read=bool(is_read),
        country_code=country_code,
        **kw,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def create_dispute_notification_for_update(
    db: Session,
    *,
    user_id: Optional[int] = None,
    supplier_id: Optional[int] = None,
    dispute=None,
    country_code: str = "OM",
    type: Optional[str] = None,
    title: str = "",
    message: str = "",
    link: Optional[str] = None,
    is_read: bool = False,
    **kw,
) -> Notification:
    return create_dispute_notification(
        db,
        user_id=user_id,
        supplier_id=supplier_id,
        dispute=dispute,
        country_code=country_code,
        type=type,
        title=title,
        message=message,
        link=link,
        is_read=is_read,
        **kw,
    )


def create_supplier_notification_preference(
    db: Session,
    *,
    supplier_id: int,
    **prefs,
) -> SupplierNotificationPreference:
    record = SupplierNotificationPreference(supplier_id=supplier_id, **prefs)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def update_supplier_dispute(db: Session, record_or_id, changes: Optional[dict] = None, **kw):
    if _is_orm(record_or_id, SupplierDispute):
        record = record_or_id
    else:
        record = db.get(SupplierDispute, int(record_or_id))
        if record is None:
            raise ValueError(f"SupplierDispute {record_or_id} not found")
    _apply_changes(record, changes or kw)
    db.commit()
    db.refresh(record)
    return record


def update_supplier_notification_preference(db: Session, record_or_id, changes: Optional[dict] = None, **kw):
    if _is_orm(record_or_id, SupplierNotificationPreference):
        record = record_or_id
    else:
        record = db.get(SupplierNotificationPreference, int(record_or_id))
        if record is None:
            raise ValueError(f"SupplierNotificationPreference {record_or_id} not found")
    _apply_changes(record, changes or kw)
    db.commit()
    db.refresh(record)
    return record


def bulk_update_disputes(db: Session, rows_or_ids, changes: Optional[dict] = None, **kw):
    """Bulk-apply ``changes`` to many disputes.

    ``rows_or_ids`` may be a list of ORM rows (legacy controller form) or a list
    of integer ids (spec form). Returns the list of updated rows.
    """
    if not rows_or_ids:
        return []
    if _is_orm(rows_or_ids[0], SupplierDispute):
        records = list(rows_or_ids)
    else:
        records = db.query(SupplierDispute).filter(SupplierDispute.id.in_(rows_or_ids)).all()
    for record in records:
        _apply_changes(record, changes or kw)
    db.commit()
    return records
