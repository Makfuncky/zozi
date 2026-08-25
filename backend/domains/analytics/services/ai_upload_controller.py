"""AI Upload Controller — orchestrates background job lifecycle for AI image uploads."""
from __future__ import annotations

from fastapi import UploadFile
from infrastructure.utils.background_jobs import cancel_job, get_job, _update_job, _utcnow_iso


def create_job(*, current_user: dict, db: Session, images: list[UploadFile],
               country_code: str, model_used: str | None = None,
               prompt_hash: str | None = None) -> dict:
    """Create a new AI upload processing job."""
    from infrastructure.utils.background_jobs import enqueue_ml_job

    job_id = enqueue_ml_job(
        kind="ai_upload",
        metadata={
            "user_id": current_user.get("id"),
            "country_code": country_code,
            "model_used": model_used,
            "prompt_hash": prompt_hash,
            "image_count": len(images) if images else 0,
        },
    )
    return {"job_id": job_id, "status": "queued"}


def publish_job(*, job_id: int, current_user: dict, db: Session,
                overrides: dict | None = None) -> dict:
    """Publish a completed AI upload job, making results visible."""
    job = get_job(str(job_id))
    if job is None:
        return {"error": "job_not_found", "job_id": job_id}
    if job.get("status") != "completed":
        return {"error": "job_not_completed", "job_id": job_id, "status": job.get("status")}
    _update_job(str(job_id), status="published", published_at=_utcnow_iso(),
                published_by=current_user.get("id"), overrides=overrides or {})
    return {"job_id": job_id, "status": "published"}


def process_job(*, job_id: int) -> dict:
    """Trigger (or re-trigger) processing of a queued AI upload job."""
    job = get_job(str(job_id))
    if job is None:
        return {"error": "job_not_found", "job_id": job_id}
    if job.get("status") not in ("queued", "failed"):
        return {"error": "job_not_processable", "job_id": job_id, "status": job.get("status")}
    _update_job(str(job_id), status="running")
    return {"job_id": job_id, "status": "running"}
