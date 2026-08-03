"""
Upload Job Service — manages upload lifecycle + WebSocket push notifications
============================================================================
Each upload gets a UploadJob record that progresses through:
  queued → processing_bg → processing_ai → generating_copy → completed

Every status change pushes a real-time update via WebSocket to the supplier's    connected clients (using the canonical UserConnectionManager from services.websocket_manager).
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from data.db import get_db_session
from models.upload_job import UploadJob

logger = logging.getLogger(__name__)

# Try to import the WebSocket manager — may not be available in all contexts
_ws_manager = None


def _get_ws_manager():
    """Lazy import the WebSocket connection manager to avoid circular imports."""
    global _ws_manager
    if _ws_manager is None:
        try:
            from services.websocket_manager import user_manager  # lazy — may not be available in all contexts
            _ws_manager = user_manager
        except ImportError:
            logger.warning("WebSocket manager not available — real-time push disabled")
    return _ws_manager


# ── Job CRUD ─────────────────────────────────────────────────────────────────


def create_job(
    supplier_id: int,
    filename: str = "",
    image_url: Optional[str] = None,
    db: Optional[Session] = None,
) -> UploadJob:
    """Create a new upload job with initial 'queued' status."""
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


def update_job_status(
    job_id: int,
    status: str,
    progress: Optional[float] = None,
    db: Optional[Session] = None,
    **extra_fields,
) -> Optional[UploadJob]:
    """Update an upload job's status and progress, then push WS update."""
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


def get_supplier_jobs(
    supplier_id: int,
    limit: int = 20,
    offset: int = 0,
    status: Optional[str] = None,
    db: Optional[Session] = None,
) -> Dict[str, Any]:
    """Get upload jobs for a supplier with pagination."""
    close_db = db is None
    if close_db:
        db = get_db_session()
    try:
        query = db.query(UploadJob).filter(UploadJob.supplier_id == supplier_id)
        if status:
            query = query.filter(UploadJob.status == status)
        total = query.count()
        jobs = (
            query.order_by(UploadJob.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return {
            "items": [j.to_dict() for j in jobs],
            "total": total,
        }
    finally:
        if close_db:
            db.close()


def get_job_stats(supplier_id: int, db: Optional[Session] = None) -> Dict[str, Any]:
    """Get aggregate stats for a supplier's upload jobs."""
    close_db = db is None
    if close_db:
        db = get_db_session()
    try:
        total = db.query(UploadJob).filter(UploadJob.supplier_id == supplier_id).count()
        completed = (
            db.query(UploadJob)
            .filter(UploadJob.supplier_id == supplier_id, UploadJob.status == "completed")
            .count()
        )
        failed = (
            db.query(UploadJob)
            .filter(UploadJob.supplier_id == supplier_id, UploadJob.status == "failed")
            .count()
        )
        in_progress = total - completed - failed

        # Average time for last 20 completed jobs
        avg_time = 0.0
        recent = (
            db.query(UploadJob)
            .filter(
                UploadJob.supplier_id == supplier_id,
                UploadJob.status == "completed",
                UploadJob.total_duration_ms.isnot(None),
            )
            .order_by(UploadJob.completed_at.desc())
            .limit(20)
            .all()
        )
        if recent:
            durations = [j.total_duration_ms for j in recent if j.total_duration_ms]
            avg_time = sum(durations) / len(durations) if durations else 0.0

        # Strategy win counts
        strategy_wins = {}
        winner_jobs = (
            db.query(UploadJob)
            .filter(
                UploadJob.supplier_id == supplier_id,
                UploadJob.strategy_winner.isnot(None),
            )
            .all()
        )
        for j in winner_jobs:
            s = j.strategy_winner or "unknown"
            strategy_wins[s] = strategy_wins.get(s, 0) + 1

        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "in_progress": in_progress,
            "avg_time_ms": round(avg_time, 1),
            "strategy_wins": strategy_wins,
        }
    finally:
        if close_db:
            db.close()


# ── WebSocket Push ───────────────────────────────────────────────────────────


def _push_update(job: UploadJob, event_type: str = "job.updated") -> None:
    """Push a real-time update via WebSocket to the supplier's connected clients."""
    manager = _get_ws_manager()
    if manager is None:
        return
    try:
        payload = {
            "type": event_type,
            "job": job.to_dict(),
        }
        # Dispatch via the user's notification WebSocket
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                loop.create_task(
                    manager.broadcast_to_user(job.supplier_id, payload)
                )
            else:
                logger.debug("No running event loop for WS push")
        except RuntimeError:
            logger.debug("No event loop available for WS push")
    except Exception as exc:
        logger.warning("Failed to push WS update for job %s: %s", job.id, exc)


# ── Convenience wrappers for pipeline steps ──────────────────────────────────


def mark_queued(job_id: int, db: Optional[Session] = None) -> Optional[UploadJob]:
    return update_job_status(job_id, "queued", progress=0, db=db)


def mark_processing_bg(job_id: int, progress: float = 20, db: Optional[Session] = None) -> Optional[UploadJob]:
    return update_job_status(job_id, "processing_bg", progress=progress, db=db)


def mark_processing_ai(job_id: int, progress: float = 50, db: Optional[Session] = None) -> Optional[UploadJob]:
    return update_job_status(job_id, "processing_ai", progress=progress, db=db)


def mark_generating_copy(job_id: int, progress: float = 75, db: Optional[Session] = None) -> Optional[UploadJob]:
    return update_job_status(job_id, "generating_copy", progress=progress, db=db)


def mark_completed(
    job_id: int,
    product_id: Optional[int] = None,
    total_duration_ms: Optional[float] = None,
    db: Optional[Session] = None,
) -> Optional[UploadJob]:
    return update_job_status(
        job_id, "completed", progress=100,
        product_id=product_id,
        completed_at=datetime.now(timezone.utc),
        total_duration_ms=total_duration_ms,
        db=db,
    )


def mark_failed(
    job_id: int,
    error_message: str,
    db: Optional[Session] = None,
) -> Optional[UploadJob]:
    return update_job_status(
        job_id, "failed",
        error_message=error_message,
        completed_at=datetime.now(timezone.utc),
        db=db,
    )
