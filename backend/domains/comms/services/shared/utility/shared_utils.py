"""Shared utility services for the comms domain.

Combines: db_write, event_bus, misc_write_service, upload_job_service, write_helpers
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Sequence, TypeVar

from sqlalchemy.orm import Session
import structlog

logger = structlog.get_logger(__name__)

# ── DB Write Helpers (from db_write.py) ───

__all__ = [
    # db_write
    "add", "add_all", "delete", "commit", "flush", "merge", "refresh",
    "execute", "begin", "begin_nested", "savepoint", "create", "instantiate",
    "bulk_insert_mappings", "bulk_save_objects", "bulk_update_mappings",
    # event_bus
    "subscribe", "publish", "publish_order_status_changed", "publish_order_refunded",
    "EVENT_ORDER_STATUS_CHANGED", "EVENT_ORDER_REFUNDED",
    # upload_job_service
    "create_job", "update_job_status", "get_supplier_jobs", "get_job_stats",
    "mark_queued", "mark_processing_bg", "mark_processing_ai",
    "mark_generating_copy", "mark_completed", "mark_failed",
    # write_helpers
    "add_and_flush", "commit_and_refresh", "commit_only", "delete_only", "flush_only",
    # misc_write_service
    "soft_delete_record", "restore_record", "hard_delete_record", "reset_demo_data",
]


def create(db: Session, model: Any, *args, **fields) -> Any:
    """Construct a new ORM row, add it, commit and refresh in one step."""
    instance = model(*args, **fields)
    db.add(instance)
    db.commit()
    db.refresh(instance)
    return instance


def instantiate(db: Session, model: Any, *args, **fields) -> Any:
    """Construct an ORM instance and stage it with Session.add (no commit)."""
    instance = model(*args, **fields)
    db.add(instance)
    return instance


def add(db: Session, instance: Any, *args, **kwargs) -> None:
    db.add(instance, *args, **kwargs)


def add_all(db: Session, instances: Sequence, *args, **kwargs) -> None:
    db.add_all(instances, *args, **kwargs)


def delete(db: Session, instance: Any, *args, **kwargs) -> None:
    db.delete(instance, *args, **kwargs)


def commit(db: Session, *args, **kwargs) -> None:
    db.commit(*args, **kwargs)


def flush(db: Session, objects: Optional[Sequence] = None, *args, **kwargs) -> None:
    if objects is None:
        db.flush(*args, **kwargs)
    else:
        db.flush(objects, *args, **kwargs)


def merge(db: Session, instance: Any, *args, **kwargs) -> Any:
    return db.merge(instance, *args, **kwargs)


def refresh(db: Session, instance: Any, attribute_names=None, *args, **kwargs) -> None:
    if attribute_names is None:
        db.refresh(instance, *args, **kwargs)
    else:
        db.refresh(instance, attribute_names, *args, **kwargs)


def execute(db: Session, *args, **kwargs):
    return db.execute(*args, **kwargs)


def begin(db: Session, *args, **kwargs):
    return db.begin(*args, **kwargs)


def begin_nested(db: Session, *args, **kwargs):
    return db.begin_nested(*args, **kwargs)


def savepoint(db: Session, *args, **kwargs):
    return db.savepoint(*args, **kwargs)


def bulk_insert_mappings(db: Session, model, mappings: Sequence, *args, **kwargs) -> None:
    db.bulk_insert_mappings(model, mappings, *args, **kwargs)


def bulk_save_objects(db: Session, objects: Sequence, *args, **kwargs) -> None:
    db.bulk_save_objects(objects, *args, **kwargs)


def bulk_update_mappings(db: Session, model, mappings: Sequence, *args, **kwargs) -> None:
    db.bulk_update_mappings(model, mappings, *args, **kwargs)


# ── Event Bus (from event_bus.py) ───

_subscribers: Dict[str, List[Callable[[dict], None]]] = {}

EVENT_ORDER_STATUS_CHANGED = "order.status_changed"
EVENT_ORDER_REFUNDED = "order.refunded"


def subscribe(event_type: str, handler: Callable[[dict], None]) -> None:
    _subscribers.setdefault(event_type, []).append(handler)


def publish(event_type: str, payload: dict) -> None:
    for handler in list(_subscribers.get(event_type, [])):
        try:
            handler(payload)
        except Exception:
            logger.exception("event handler failed for %s", event_type)


def publish_order_status_changed(order_id: int, status: str, old_status: str | None = None) -> None:
    publish(EVENT_ORDER_STATUS_CHANGED, {"order_id": order_id, "status": status, "old_status": old_status})


def publish_order_refunded(order_id: int, source: str = "admin") -> None:
    publish(EVENT_ORDER_REFUNDED, {"order_id": order_id, "source": source})


# ── Write Helpers (from write_helpers.py) ───

_M = TypeVar("_M")


def add_and_flush(db: Session, obj: _M) -> _M:
    db.add(obj)
    db.flush()
    return obj


def commit_and_refresh(db: Session, obj: _M) -> _M:
    db.commit()
    db.refresh(obj)
    return obj


def commit_only(db: Session) -> None:
    db.commit()


def delete_only(db: Session, obj: _M) -> None:
    db.delete(obj)
    db.commit()


def flush_only(db: Session, obj: _M | None = None) -> None:
    if obj is not None:
        db.add(obj)
    db.flush()


# ── Misc Write Service (from misc_write_service.py) ───

from domains.governance.ports import RolePermissionSetting, SupplierDispute
from domains.promotions.models.promotions import Banner
from infrastructure.database.seed import _ensure_demo_user, _seed_password
# TODO: Module not yet created
# from domains.finance.services.cash_write_service import create_cash_account, create_cash_transaction
from infrastructure.utils.config import settings
from infrastructure.utils.soft_delete import (
    _has_soft_delete as has_soft_delete,
    _now as _soft_now,
    hard_delete as _soft_delete_hard_delete,
    restore as _soft_delete_restore,
    soft_delete as _soft_delete_soft_delete,
)


def soft_delete_record(db, record, acting_user, reason=None):
    _soft_delete_soft_delete(db, type(record), record.id, acting_user, reason)


def restore_record(db, record, acting_user):
    _soft_delete_restore(db, type(record), record.id, acting_user)


def hard_delete_record(db, record, acting_user, reason=None):
    _soft_delete_hard_delete(db, type(record), record.id, acting_user, reason)


def reset_demo_data(db: Session, *, country_code: Optional[str] = None) -> dict:
    if str(getattr(settings, "app_env", "")).strip().lower() == "production":
        raise RuntimeError("reset_demo_data is disabled in production; it seeds hardcoded demo accounts.")

    deleted: dict = {}

    def _safe_clear(Model, label):
        try:
            rows = db.query(Model)
            if country_code is not None and hasattr(Model, "country_code"):
                rows = rows.filter(Model.country_code == country_code)
            count = rows.count()
            if count and _has_soft_delete(Model):
                rows.update(
                    {Model.is_deleted: True, Model.deleted_at: _soft_now()},
                    synchronize_session=False,
                )
            elif count:
                rows.delete(synchronize_session=False)
            db.commit()
            deleted[label] = count
        except Exception as exc:
            db.rollback()
            logger.warning("reset_demo_data_clear_failed", label=label, error=str(exc))
            deleted[label] = "error"

    _safe_clear(Banner, "banners")
    _safe_clear(SupplierDispute, "supplier_disputes")
    _safe_clear(RolePermissionSetting, "role_permission_settings")

    reseeded = 0
    try:
        _ensure_demo_user(db, email="admin@zozi.om", username="admin", password=_seed_password("SEED_ADMIN_PASSWORD"), role="admin", log_label="admin")
        _ensure_demo_user(db, email="supplier@zozi.om", username="supplier", password=_seed_password("SEED_SUPPLIER_PASSWORD"), role="supplier", log_label="supplier")
        _ensure_demo_user(db, email="customer@zozi.om", username="customer", password=_seed_password("SEED_CUSTOMER_PASSWORD"), role="customer", log_label="customer")
        reseeded = 3
    except Exception as exc:
        db.rollback()
        logger.warning("reset_demo_data_reseed_failed", error=str(exc))

    return {"deleted": deleted, "reseeded": reseeded}


# ── Upload Job Service (from upload_job_service.py) ───

from infrastructure.database.database import get_db_session
from domains.catalog.models.upload_job import UploadJob

_ws_manager = None


def _get_ws_manager():
    global _ws_manager
    if _ws_manager is None:
        try:
            from domains.comms.services.messaging.realtime.websocket_manager import user_manager
            _ws_manager = user_manager
        except ImportError:
            logger.warning("WebSocket manager not available — real-time push disabled")
    return _ws_manager


def create_job(supplier_id: int, filename: str = "", image_url: Optional[str] = None, db: Optional[Session] = None) -> UploadJob:
    close_db = db is None
    if close_db:
        db = get_db_session()
    try:
        job = UploadJob(
            supplier_id=supplier_id,
            filename=filename,
            status="queued",
            progress=0.0,
            started_at=datetime.now(timezone.utc),
            image_url=image_url,
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        _push_update(job, "job.created")
        return job
    finally:
        if close_db:
            db.close()


def update_job_status(job_id: int, status: str, progress: Optional[float] = None, db: Optional[Session] = None, **extra_fields) -> Optional[UploadJob]:
    close_db = db is None
    if close_db:
        db = get_db_session()
    try:
        job = db.query(UploadJob).filter(UploadJob.id == job_id).first()
        if not job:
            logger.warning("UploadJob %s not found", job_id)
            return None
        job.status = status
        if progress is not None:
            job.progress = min(100.0, max(0.0, progress))
        if status == "completed":
            job.completed_at = datetime.now(timezone.utc)
            job.progress = 100.0
        if status == "failed":
            job.error_message = extra_fields.pop("error_message", job.error_message)
        for key, value in extra_fields.items():
            if hasattr(job, key):
                setattr(job, key, value)
        job.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(job)
        _push_update(job, "job.updated")
        return job
    except Exception as exc:
        logger.exception("Failed to update UploadJob %s: %s", job_id, exc)
        return None
    finally:
        if close_db:
            db.close()


def get_supplier_jobs(supplier_id: int, limit: int = 20, offset: int = 0, status: Optional[str] = None, db: Optional[Session] = None) -> Dict[str, Any]:
    close_db = db is None
    if close_db:
        db = get_db_session()
    try:
        query = db.query(UploadJob).filter(UploadJob.supplier_id == supplier_id)
        if status:
            query = query.filter(UploadJob.status == status)
        total = query.count()
        jobs = query.order_by(UploadJob.created_at.desc()).offset(offset).limit(limit).all()
        return {"items": [j.to_dict() for j in jobs], "total": total}
    finally:
        if close_db:
            db.close()


def get_job_stats(supplier_id: int, db: Optional[Session] = None) -> Dict[str, Any]:
    close_db = db is None
    if close_db:
        db = get_db_session()
    try:
        total = db.query(UploadJob).filter(UploadJob.supplier_id == supplier_id).count()
        completed = db.query(UploadJob).filter(UploadJob.supplier_id == supplier_id, UploadJob.status == "completed").count()
        failed = db.query(UploadJob).filter(UploadJob.supplier_id == supplier_id, UploadJob.status == "failed").count()
        in_progress = total - completed - failed
        avg_time = 0.0
        recent = db.query(UploadJob).filter(UploadJob.supplier_id == supplier_id, UploadJob.status == "completed", UploadJob.total_duration_ms.isnot(None)).order_by(UploadJob.completed_at.desc()).limit(20).all()
        if recent:
            durations = [j.total_duration_ms for j in recent if j.total_duration_ms]
            avg_time = sum(durations) / len(durations) if durations else 0.0
        strategy_wins = {}
        winner_jobs = db.query(UploadJob).filter(UploadJob.supplier_id == supplier_id, UploadJob.strategy_winner.isnot(None)).all()
        for j in winner_jobs:
            s = j.strategy_winner or "unknown"
            strategy_wins[s] = strategy_wins.get(s, 0) + 1
        return {"total": total, "completed": completed, "failed": failed, "in_progress": in_progress, "avg_time_ms": round(avg_time, 1), "strategy_wins": strategy_wins}
    finally:
        if close_db:
            db.close()


def _push_update(job: UploadJob, event_type: str = "job.updated") -> None:
    manager = _get_ws_manager()
    if manager is None:
        return
    try:
        payload = {"type": event_type, "job": job.to_dict()}
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                loop.create_task(manager.broadcast_to_user(job.supplier_id, payload))
            else:
                logger.debug("No running event loop for WS push")
        except RuntimeError:
            logger.debug("No event loop available for WS push")
    except Exception as exc:
        logger.warning("Failed to push WS update for job %s: %s", job.id, exc)


def mark_queued(job_id: int, db: Optional[Session] = None) -> Optional[UploadJob]:
    return update_job_status(job_id, "queued", progress=0, db=db)


def mark_processing_bg(job_id: int, progress: float = 20, db: Optional[Session] = None) -> Optional[UploadJob]:
    return update_job_status(job_id, "processing_bg", progress=progress, db=db)


def mark_processing_ai(job_id: int, progress: float = 50, db: Optional[Session] = None) -> Optional[UploadJob]:
    return update_job_status(job_id, "processing_ai", progress=progress, db=db)


def mark_generating_copy(job_id: int, progress: float = 75, db: Optional[Session] = None) -> Optional[UploadJob]:
    return update_job_status(job_id, "generating_copy", progress=progress, db=db)


def mark_completed(job_id: int, product_id: Optional[int] = None, total_duration_ms: Optional[float] = None, db: Optional[Session] = None) -> Optional[UploadJob]:
    return update_job_status(job_id, "completed", progress=100, product_id=product_id, completed_at=datetime.now(timezone.utc), total_duration_ms=total_duration_ms, db=db)


def mark_failed(job_id: int, error_message: str, db: Optional[Session] = None) -> Optional[UploadJob]:
    return update_job_status(job_id, "failed", error_message=error_message, completed_at=datetime.now(timezone.utc), db=db)
