"""Soft-delete helper — centralized archive/restore/bulk operations for all entities."""

from datetime import datetime, timezone
from typing import Any, List, Optional, Tuple, Type, Union

from fastapi import HTTPException
from sqlalchemy.orm import Session

from utils.audit_log import AuditAction, audit_log


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _has_soft_delete(model: Type[Any]) -> bool:
    return hasattr(model, "is_deleted") and hasattr(model, "deleted_at")


def soft_delete(
    db: Session,
    model: Type[Any],
    record_id: Union[int, str],
    acting_user: dict,
    reason: Optional[str] = None,
    skip_audit: bool = False,
) -> Any:
    """Mark a record as soft-deleted (archived).

    Sets is_deleted=True, deleted_at=now, deleted_by=acting_user, deletion_reason=reason.
    """
    if not _has_soft_delete(model):
        raise HTTPException(status_code=400, detail=f"Model {model.__name__} does not support soft delete")
    record = db.query(model).filter(model.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail=f"{model.__name__} not found")
    if bool(getattr(record, "is_deleted")):
        raise HTTPException(status_code=400, detail=f"{model.__name__} is already archived")
    setattr(record, "is_deleted", True)
    setattr(record, "deleted_at", _now())
    setattr(record, "deleted_by", acting_user.get("id"))
    if reason:
        setattr(record, "deletion_reason", reason)
    db.commit()
    if not skip_audit:
        audit_log(
            db=db,
            action=AuditAction.get_archive_action(model.__name__),
            user_id=acting_user.get("id"),
            username=acting_user.get("username"),
            user_role=acting_user.get("role"),
            resource_type=model.__tablename__,
            resource_id=record_id,
            details={"action": "archive", "reason": reason, "name": str(getattr(record, "name", record_id))},
            status="success",
        )
    return record


def restore(
    db: Session,
    model: Type[Any],
    record_id: Union[int, str],
    acting_user: dict,
    skip_audit: bool = False,
) -> Any:
    """Restore a soft-deleted record.

    Sets is_deleted=False, deleted_at=NULL, restore_at=now, restore_by=acting_user.
    """
    if not _has_soft_delete(model):
        raise HTTPException(status_code=400, detail=f"Model {model.__name__} does not support soft delete")
    record = db.query(model).filter(model.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail=f"{model.__name__} not found")
    if not bool(getattr(record, "is_deleted")):
        raise HTTPException(status_code=400, detail=f"{model.__name__} is not archived")
    setattr(record, "is_deleted", False)
    setattr(record, "deleted_at", None)
    setattr(record, "deleted_by", None)
    setattr(record, "restore_at", _now())
    setattr(record, "restore_by", acting_user.get("id"))
    db.commit()
    if not skip_audit:
        audit_log(
            db=db,
            action=AuditAction.get_restore_action(model.__name__),
            user_id=acting_user.get("id"),
            username=acting_user.get("username"),
            user_role=acting_user.get("role"),
            resource_type=model.__tablename__,
            resource_id=record_id,
            details={"action": "restore", "name": str(getattr(record, "name", record_id))},
            status="success",
        )
    return record


def hard_delete(
    db: Session,
    model: Type[Any],
    record_id: Union[int, str],
    acting_user: dict,
    reason: Optional[str] = None,
) -> None:
    """Permanently remove a record from the database (super admin only)."""
    record = db.query(model).filter(model.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail=f"{model.__name__} not found")
    audit_log(
        db=db,
        action=AuditAction.PERMANENT_DELETE,
        user_id=acting_user.get("id"),
        username=acting_user.get("username"),
        user_role=acting_user.get("role"),
        resource_type=model.__tablename__,
        resource_id=record_id,
        details={"action": "permanent_delete", "reason": reason, "name": str(getattr(record, "name", record_id))},
        status="success",
    )
    if _has_soft_delete(model):
        db.query(model).filter(model.id == record_id).update({model.is_deleted: True, model.deleted_at: _now()})
    else:
        db.delete(record)
    db.commit()


def bulk_soft_delete(
    db: Session,
    model: Type[Any],
    record_ids: List[Union[int, str]],
    acting_user: dict,
    reason: Optional[str] = None,
) -> dict:
    """Archive multiple records at once."""
    archived = 0
    errors = []
    for rid in record_ids:
        try:
            soft_delete(db, model, rid, acting_user, reason, skip_audit=True)
            archived += 1
        except HTTPException as e:
            errors.append({"id": rid, "error": e.detail})
    if archived:
        audit_log(
            db=db,
            action=AuditAction.get_bulk_archive_action(model.__name__),
            user_id=acting_user.get("id"),
            username=acting_user.get("username"),
            user_role=acting_user.get("role"),
            resource_type=model.__tablename__,
            resource_id=None,
            details={"action": "bulk_archive", "count": archived, "reason": reason, "errors": errors},
            status="success",
        )
    return {"archived": archived, "errors": errors}


def bulk_restore(
    db: Session,
    model: Type[Any],
    record_ids: List[Union[int, str]],
    acting_user: dict,
) -> dict:
    """Restore multiple archived records at once."""
    restored = 0
    errors = []
    for rid in record_ids:
        try:
            restore(db, model, rid, acting_user, skip_audit=True)
            restored += 1
        except HTTPException as e:
            errors.append({"id": rid, "error": e.detail})
    if restored:
        audit_log(
            db=db,
            action=AuditAction.get_bulk_restore_action(model.__name__),
            user_id=acting_user.get("id"),
            username=acting_user.get("username"),
            user_role=acting_user.get("role"),
            resource_type=model.__tablename__,
            resource_id=None,
            details={"action": "bulk_restore", "count": restored, "errors": errors},
            status="success",
        )
    return {"restored": restored, "errors": errors}


