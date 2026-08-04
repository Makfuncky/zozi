
"""Lightweight background job execution with Redis-backed status storage.

Supports per-kind concurrency limits, retry, dedicated ML worker pools,
backpressure, job deduplication (idempotency keys), and distributed locking
so heavy CPU/RAM work never starves the HTTP request path.
"""

import hashlib
import json
import logging
import os
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Optional

from fastapi.encoders import jsonable_encoder

from utils.config import settings

logger = logging.getLogger(__name__)

_JOB_LOCK = threading.RLock()
_MEMORY_JOBS: dict[str, tuple[float, dict[str, Any]]] = {}
_RUNNING_JOBS: set[str] = set()  # tracks running job ids for idempotency

# ── Per-kind concurrency governors ──────────────────────────────────────────
# ML/heavy work gets its own pool so a burst of image processing doesn't
# consume workers needed for fast jobs (cache clear, email send, etc.).
_FAST_WORKERS = max(settings.background_job_workers or 2, 1)
_ML_WORKERS = max(getattr(settings, "ml_workers", 1), 1)

_FAST_EXECUTOR = ThreadPoolExecutor(max_workers=_FAST_WORKERS, thread_name_prefix="bg-fast")
_ML_EXECUTOR = ThreadPoolExecutor(max_workers=_ML_WORKERS, thread_name_prefix="bg-ml")

# Active job counters per kind for backpressure.
_kind_active: dict[str, int] = {}
_kind_max: dict[str, int] = {}

def _init_kind_limits():
    global _kind_max
    _kind_max = {
        "ml": _ML_WORKERS,           # background removal, AI analysis, angle generation
        "bulk_import": _ML_WORKERS,  # CSV / bulk product import
        "ai_copy": _FAST_WORKERS,    # copy generation (Ollama, CPU-bound but lightweight)
        "default": _FAST_WORKERS,    # everything else
    }

_init_kind_limits()


class JobKind(str, Enum):
    ML = "ml"
    BULK_IMPORT = "bulk_import"
    AI_COPY = "ai_copy"
    EXPORT = "export"
    EMAIL = "email"
    NOTIFICATION = "notification"
    DEFAULT = "default"


def _get_executor(kind: str) -> ThreadPoolExecutor:
    if kind in (JobKind.ML, JobKind.BULK_IMPORT):
        return _ML_EXECUTOR
    return _FAST_EXECUTOR


def _should_run_inline() -> bool:
    return settings.app_env == "test" or bool(os.environ.get("PYTEST_CURRENT_TEST"))


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).replace(tzinfo=None).isoformat()


def _job_key(job_id: str) -> str:
    return f"background-jobs:{job_id}"


def _get_redis_client():
    if _should_run_inline():
        return None
    try:
        from utils.auth import _get_redis
        return _get_redis()
    except Exception:
        return None


def _prune_memory_jobs_locked(now: float | None = None) -> None:
    current = now if now is not None else time.monotonic()
    expired_ids = [
        job_id for job_id, (expires_at, _) in _MEMORY_JOBS.items()
        if expires_at <= current
    ]
    for job_id in expired_ids:
        _MEMORY_JOBS.pop(job_id, None)


def _store_job(payload: dict[str, Any]) -> None:
    redis_client = _get_redis_client()
    if redis_client is not None:
        try:
            redis_client.setex(
                _job_key(payload["id"]),
                settings.background_job_ttl_seconds,
                json.dumps(payload, default=str),
            )
            return
        except Exception:
            pass

    with _JOB_LOCK:
        now = time.monotonic()
        _prune_memory_jobs_locked(now)
        ttl = max(int(settings.background_job_ttl_seconds or 0), 1)
        _MEMORY_JOBS[payload["id"]] = (now + ttl, dict(payload))


def get_job(job_id: str) -> dict[str, Any] | None:
    redis_client = _get_redis_client()
    if redis_client is not None:
        try:
            raw = redis_client.get(_job_key(job_id))
            if raw:
                if isinstance(raw, (bytes, bytearray)):
                    raw = raw.decode("utf-8")
                return json.loads(raw)
        except Exception:
            pass

    with _JOB_LOCK:
        now = time.monotonic()
        _prune_memory_jobs_locked(now)
        cached = _MEMORY_JOBS.get(job_id)
        if cached is None:
            return None
        _, job = cached
        return dict(job)


def _update_job(job_id: str, **changes: Any) -> dict[str, Any] | None:
    payload = get_job(job_id)
    if payload is None:
        return None
    payload.update(changes)
    _store_job(payload)
    return payload


def _compute_idempotency_key(kind: str, metadata: dict[str, Any] | None) -> str | None:
    if not metadata:
        return None
    dedup_key = metadata.get("idempotency_key")
    if dedup_key:
        raw = f"{kind}:{dedup_key}"
        return hashlib.sha256(raw.encode()).hexdigest()
    return None


def _check_idempotency(dedup_key: str, ttl: int) -> dict[str, Any] | None:
    """Check if a job with this dedup key is running or recently completed."""
    redis_client = _get_redis_client()
    dedup_storage_key = f"bg-dedup:{dedup_key}"

    if redis_client is not None:
        try:
            existing = redis_client.get(dedup_storage_key)
            if existing:
                raw = existing.decode("utf-8") if isinstance(existing, bytes) else existing
                return json.loads(raw)
            return None
        except Exception:
            pass

    with _JOB_LOCK:
        for _, (expires_at, job) in list(_MEMORY_JOBS.items()):
            if job.get("dedup_key") == dedup_key:
                if time.monotonic() < expires_at:
                    return dict(job)
                break
    return None


def _set_dedup_key(dedup_key: str, payload: dict[str, Any], ttl: int) -> None:
    redis_client = _get_redis_client()
    storage_key = f"bg-dedup:{dedup_key}"
    if redis_client is not None:
        try:
            redis_client.setex(storage_key, ttl, json.dumps(payload, default=str))
            return
        except Exception:
            pass


def _clear_dedup_key(dedup_key: str) -> None:
    redis_client = _get_redis_client()
    if redis_client is not None:
        try:
            redis_client.delete(f"bg-dedup:{dedup_key}")
        except Exception:
            pass


def enqueue_job(
    *,
    kind: str = JobKind.DEFAULT,
    owner_user_id: int | None = None,
    owner_role: str | None = None,
    func: Callable[[], Any],
    metadata: dict[str, Any] | None = None,
    max_retries: int = 0,
    idempotency_key: str | None = None,
    lock_ttl: int = 300,
) -> dict[str, Any]:
    """Enqueue a background job and return its payload immediately.

    Parameters
    ----------
    kind:
        Job kind — determines which thread pool runs it and the concurrency cap.
    owner_user_id, owner_role:
        Identity of the requesting user (for audit).
    func:
        Zero-argument callable that does the actual work.
    metadata:
        Arbitrary JSON-serialisable data attached to the job.
    max_retries:
        Number of automatic retries on failure (default 0 = no retry).
    idempotency_key:
        Optional key for deduplication. If a job with the same key is already
        running or completed within lock_ttl seconds, this enqueue is a no-op
        that returns the existing job payload.
    lock_ttl:
        Seconds to consider a completed job as still valid for dedup.
    """
    meta = metadata or {}

    # ── Idempotency check ──────────────────────────────────────────────────
    if idempotency_key or meta.get("idempotency_key"):
        dedup_raw = _compute_idempotency_key(kind, {**meta, "idempotency_key": idempotency_key or meta["idempotency_key"]})
        if dedup_raw:
            existing = _check_idempotency(dedup_raw, lock_ttl)
            if existing is not None:
                return existing

    job_id = uuid.uuid4().hex
    dedup_key = _compute_idempotency_key(kind, {**meta, "idempotency_key": idempotency_key or meta.get("idempotency_key")}) if (idempotency_key or meta.get("idempotency_key")) else None

    payload: dict[str, Any] = {
        "id": job_id,
        "kind": kind,
        "status": "queued",
        "owner_user_id": owner_user_id,
        "owner_role": owner_role,
        "metadata": meta,
        "result": None,
        "error": None,
        "created_at": _utcnow_iso(),
        "started_at": None,
        "finished_at": None,
        "max_retries": max_retries,
        "retry_count": 0,
        "dedup_key": dedup_key,
    }
    _store_job(payload)

    if dedup_key:
        _set_dedup_key(dedup_key, payload, lock_ttl)

    def _runner() -> None:
        kind_max = _kind_max.get(kind, _kind_max["default"])

        # ── Backpressure: reject if this kind is saturated ──────────────
        with _JOB_LOCK:
            active = _kind_active.get(kind, 0)
            if active >= kind_max:
                _update_job(
                    job_id,
                    status="rejected",
                    error=f"Too many concurrent {kind} jobs (limit={kind_max})",
                    finished_at=_utcnow_iso(),
                )
                return
            _kind_active[kind] = active + 1

        try:
            _do_run(job_id, kind, func, max_retries)
        finally:
            with _JOB_LOCK:
                _kind_active[kind] = max(_kind_active.get(kind, 1) - 1, 0)

    if _should_run_inline():
        _runner()
        return get_job(job_id) or payload

    executor = _get_executor(kind)
    executor.submit(_runner)
    return payload


def _do_run(job_id: str, kind: str, func: Callable[[], Any], max_retries: int) -> None:
    _update_job(job_id, status="running", started_at=_utcnow_iso(), error=None)
    retries_left = max_retries
    while True:
        try:
            result = func()
            _update_job(
                job_id,
                status="completed",
                result=jsonable_encoder(result),
                finished_at=_utcnow_iso(),
            )
            # Keep dedup key alive so subsequent identical enqueues are rejected
            return
        except Exception as exc:
            logger.exception("Background job %s failed (retries_left=%d)", job_id, retries_left)
            if retries_left > 0:
                retries_left -= 1
                _update_job(
                    job_id,
                    status="retrying",
                    error=str(exc),
                    retry_count=max_retries - retries_left,
                )
                time.sleep(2 ** (max_retries - retries_left))  # exponential backoff
                continue
            _update_job(
                job_id,
                status="failed",
                error=str(exc),
                finished_at=_utcnow_iso(),
                retry_count=max_retries,
            )
            # Clear dedup on terminal failure so job can be retried manually
            job_data = get_job(job_id)
            if job_data and job_data.get("dedup_key"):
                _clear_dedup_key(job_data["dedup_key"])
            return


# ── Convenience wrappers for common job kinds ──────────────────────────────

def enqueue_ml_job(
    *,
    owner_user_id: int | None = None,
    owner_role: str | None = None,
    func: Callable[[], Any],
    metadata: dict[str, Any] | None = None,
    max_retries: int = 1,
) -> dict[str, Any]:
    """Enqueue an ML / heavy-compute job (background removal, AI analysis, angle gen)."""
    return enqueue_job(
        kind=JobKind.ML,
        owner_user_id=owner_user_id,
        owner_role=owner_role,
        func=func,
        metadata=metadata,
        max_retries=max_retries,
    )


def enqueue_bulk_import_job(
    *,
    owner_user_id: int | None = None,
    owner_role: str | None = None,
    func: Callable[[], Any],
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Enqueue a bulk product import job."""
    return enqueue_job(
        kind=JobKind.BULK_IMPORT,
        owner_user_id=owner_user_id,
        owner_role=owner_role,
        func=func,
        metadata=metadata,
        max_retries=0,
    )


def cancel_job(job_id: str) -> bool:
    """Cancel a queued or running job if possible.

    Returns True if the job was marked as cancelled, False if not found
    or already completed.
    """
    job_data = get_job(job_id)
    if job_data is None:
        return False
    if job_data["status"] in ("completed", "failed", "cancelled"):
        return False
    _update_job(job_id, status="cancelled", finished_at=_utcnow_iso())
    if job_data.get("dedup_key"):
        _clear_dedup_key(job_data["dedup_key"])
    return True


def get_running_jobs(kind: str | None = None) -> list[dict[str, Any]]:
    """Return all currently running jobs, optionally filtered by kind."""
    results = []
    with _JOB_LOCK:
        for _, (_, job) in list(_MEMORY_JOBS.items()):
            if job.get("status") == "running":
                if kind is None or job.get("kind") == kind:
                    results.append(dict(job))
    return results


def job_stats() -> dict[str, Any]:
    """Return summary statistics about the background job subsystem."""
    with _JOB_LOCK:
        active = dict(_kind_active)
    total_active = sum(active.values())
    max_concurrent = sum(_kind_max.values())
    return {
        "running": total_active,
        "max_concurrent": max_concurrent,
        "active_by_kind": active,
        "kind_limits": dict(_kind_max),
    }
