"""Lightweight background job execution with Redis-backed status storage."""
from __future__ import annotations

import json
import logging
import os
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Any, Callable

from fastapi.encoders import jsonable_encoder

from utils.config import settings

logger = logging.getLogger(__name__)

_JOB_LOCK = threading.RLock()
_MEMORY_JOBS: dict[str, tuple[float, dict[str, Any]]] = {}
_EXECUTOR = ThreadPoolExecutor(max_workers=max(settings.background_job_workers, 1))


def _should_run_inline() -> bool:
    return settings.app_env == "test" or bool(os.environ.get("PYTEST_CURRENT_TEST"))


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).replace(tzinfo=None).isoformat()


def _job_key(job_id: str) -> str:
    return f"background-jobs:{job_id}"


def _get_redis_client():
    try:
        from utils.auth import _get_redis

        return _get_redis()
    except Exception:
        return None


def _prune_memory_jobs_locked(now: float | None = None) -> None:
    current = now if now is not None else time.monotonic()
    expired_ids = [job_id for job_id, (expires_at, _) in _MEMORY_JOBS.items() if expires_at <= current]
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


def enqueue_job(
    *,
    kind: str,
    owner_user_id: int | None,
    owner_role: str | None,
    func: Callable[[], Any],
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    job_id = uuid.uuid4().hex
    payload = {
        "id": job_id,
        "kind": kind,
        "status": "queued",
        "owner_user_id": owner_user_id,
        "owner_role": owner_role,
        "metadata": metadata or {},
        "result": None,
        "error": None,
        "created_at": _utcnow_iso(),
        "started_at": None,
        "finished_at": None,
    }
    _store_job(payload)

    def _runner() -> None:
        _update_job(job_id, status="running", started_at=_utcnow_iso(), error=None)
        try:
            result = func()
        except Exception as exc:
            logger.exception("Background job %s failed", job_id)
            _update_job(
                job_id,
                status="failed",
                error=str(exc),
                finished_at=_utcnow_iso(),
            )
            return

        _update_job(
            job_id,
            status="completed",
            result=jsonable_encoder(result),
            finished_at=_utcnow_iso(),
        )

    if _should_run_inline():
        _runner()
        return get_job(job_id) or payload

    _EXECUTOR.submit(_runner)
    return payload

