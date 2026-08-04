"""In-memory async job store for slow AI copy generation.

CPU-bound LLM copy generation (EN via phi3, AR via qwen2.5) takes ~60-90s on a
VPS, which is far too slow to block a supplier's upload request. This module
runs that work as a fire-and-forget asyncio task and lets the frontend poll for
the result by job id.

The store is intentionally lightweight (a module-level dict). Jobs are pruned
after ``_JOB_TTL_SECONDS`` so memory stays bounded even with many suppliers.
For a multi-worker / multi-process deployment this should be swapped for Redis,
but the public API (enqueue / get) stays the same.
"""

import asyncio
import logging
import time
import uuid
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

_JOBS: Dict[str, Dict[str, Any]] = {}
_JOB_TTL_SECONDS = 900  # 15 min
_MAX_JOBS = 500


def _prune() -> None:
    now = time.time()
    stale = [jid for jid, j in _JOBS.items() if now - j["created_at"] > _JOB_TTL_SECONDS]
    for jid in stale:
        _JOBS.pop(jid, None)
    # Hard cap: drop oldest if we somehow exceed the ceiling.
    if len(_JOBS) > _MAX_JOBS:
        for jid in sorted(_JOBS, key=lambda k: _JOBS[k]["created_at"])[: len(_JOBS) - _MAX_JOBS]:
            _JOBS.pop(jid, None)


async def _run_copy_job(job_id: str, image_bytes: bytes, filename: str) -> None:
    from services.ai_variant_config import analyze_product_image

    try:
        result = await analyze_product_image(
            image_bytes, filename=filename, generate_copy=True, use_vision=True
        )
        _JOBS[job_id]["result"] = result
        _JOBS[job_id]["status"] = "done"
    except Exception as exc:  # noqa: BLE001
        logger.exception("ai_copy_jobs: job %s failed", job_id)
        _JOBS[job_id]["status"] = "error"
        _JOBS[job_id]["error"] = str(exc)
    finally:
        _JOBS[job_id]["finished_at"] = time.time()


def enqueue_copy_job(image_bytes: bytes, filename: str = "") -> str:
    """Spawn a background AI-copy generation task and return its job id."""
    _prune()
    job_id = uuid.uuid4().hex
    _JOBS[job_id] = {
        "status": "pending",
        "result": None,
        "error": None,
        "created_at": time.time(),
        "finished_at": None,
    }
    try:
        asyncio.get_running_loop().create_task(_run_copy_job(job_id, image_bytes, filename))
    except RuntimeError:
        # No running loop (shouldn't happen inside FastAPI) — mark as error.
        _JOBS[job_id]["status"] = "error"
        _JOBS[job_id]["error"] = "no event loop"
    return job_id


def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    """Return the job's public state, or None if unknown/expired."""
    job = _JOBS.get(job_id)
    if not job:
        return None
    return {
        "job_id": job_id,
        "status": job["status"],
        "result": job["result"],
        "error": job["error"],
    }

