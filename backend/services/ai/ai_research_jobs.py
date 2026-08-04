"""In-memory lightweight job tracker for async country AI research."""

import logging
import time
import uuid
from typing import Any, Optional

logger = logging.getLogger(__name__)

JOB_PREFIX = "country:ai:job"
RESULT_PREFIX = f"{JOB_PREFIX}:result"

_in_memory_store: dict[str, Any] = {}


_running_jobs_counter: int = 0


def _job_key(job_id: str) -> str:
    return f"{JOB_PREFIX}:{job_id}"


def _result_key(job_id: str) -> str:
    return f"{RESULT_PREFIX}:{job_id}"


def _cache_get_json(key: str) -> Any | None:
    return _in_memory_store.get(key)


def _cache_set_json(key: str, value: Any, ttl: int) -> None:
    _in_memory_store[key] = value


def enqueue_job(country_code: str, payload: dict[str, Any], ttl_seconds: int = 3600) -> dict[str, Any]:
    job_id = uuid.uuid4().hex
    job = {
        "job_id": job_id,
        "country_code": str(country_code).upper(),
        "status": "queued",
        "created_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "updated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "payload": payload,
        "error": None,
    }
    _cache_set_json(_job_key(job_id), job, ttl_seconds)
    return job


def get_job(job_id: str) -> Optional[dict[str, Any]]:
    return _cache_get_json(_job_key(job_id))


def mark_job_running(job_id: str, ttl_seconds: int = 3600) -> bool:
    job = get_job(job_id)
    if not job:
        return False
    job["status"] = "running"
    job["updated_at_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    _cache_set_json(_job_key(job_id), job, ttl_seconds)
    return True


def mark_job_completed(job_id: str, result: dict[str, Any], ttl_seconds: int = 3600) -> bool:
    job = get_job(job_id)
    if not job:
        return False
    job["status"] = "completed"
    job["updated_at_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    job.pop("error", None)
    _cache_set_json(_job_key(job_id), job, ttl_seconds)
    _cache_set_json(_result_key(job_id), result, ttl_seconds)
    return True


def mark_job_failed(job_id: str, error: str, ttl_seconds: int = 3600) -> bool:
    job = get_job(job_id)
    if not job:
        return False
    job["status"] = "failed"
    job["updated_at_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    job["error"] = str(error)
    _cache_set_json(_job_key(job_id), job, ttl_seconds)
    return True


def get_completed_result(job_id: str) -> Optional[dict[str, Any]]:
    job = get_job(job_id)
    if not job:
        return None
    if job.get("status") != "completed":
        return None
    return _cache_get_json(_result_key(job_id))


def count_running_jobs() -> int:
    return _running_jobs_counter


def increment_running_jobs() -> int:
    global _running_jobs_counter
    _running_jobs_counter += 1
    return _running_jobs_counter


def decrement_running_jobs() -> None:
    global _running_jobs_counter
    if _running_jobs_counter > 0:
        _running_jobs_counter -= 1