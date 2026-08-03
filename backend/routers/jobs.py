"""Authenticated background job status endpoints."""
from fastapi import APIRouter, Depends, HTTPException

from routers.auth import get_current_user
from utils.background_jobs import get_job

router = APIRouter()


def _can_view_job(job: dict, current_user: dict) -> bool:
    if current_user.get("role") in {"admin", "superadmin"}:
        return True
    owner_user_id = job.get("owner_user_id")
    return owner_user_id is not None and owner_user_id == current_user.get("id")


@router.get("/{job_id}")
def get_job_status(
    job_id: str,
    current_user: dict = Depends(get_current_user),
):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if not _can_view_job(job, current_user):
        raise HTTPException(status_code=403, detail="Not allowed to view this job")
    return job

