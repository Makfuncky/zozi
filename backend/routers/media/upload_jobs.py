"""
Upload Jobs Router — real-time upload tracking with WebSocket push
==================================================================
Provides endpoints for:
  - GET  /upload-jobs          — list jobs for current supplier
  - GET  /upload-jobs/stats    — aggregate stats
  - GET  /upload-jobs/{id}     — single job detail
  - WS   /ws/upload-jobs       — real-time WebSocket stream of job updates
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from data.db import get_db
from data.controllers_admin_controller import require_roles
from services.upload_job_service import (
    create_job,
    get_supplier_jobs,
    get_job_stats,
)
from models.upload_job import UploadJob

router = APIRouter()


@router.get("/upload-jobs")
def list_upload_jobs(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("supplier", "admin")),
):
    """List upload jobs for the authenticated supplier with pagination."""
    supplier_id = current_user["id"]
    return get_supplier_jobs(supplier_id, limit=limit, offset=offset, status=status, db=db)


@router.get("/upload-jobs/stats")
def upload_jobs_stats(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("supplier", "admin")),
):
    """Get aggregate upload job statistics for the supplier."""
    supplier_id = current_user["id"]
    return get_job_stats(supplier_id, db=db)


@router.get("/upload-jobs/{job_id}")
def get_upload_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("supplier", "admin")),
):
    """Get a single upload job with full details."""
    job = db.query(UploadJob).filter(UploadJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Upload job not found")
    if job.supplier_id != current_user["id"] and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not your upload job")
    return job.to_dict()


@router.post("/upload-jobs/start", status_code=201)
def start_upload_job(
    filename: str = Query(""),
    image_url: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("supplier", "admin")),
):
    """Start a new upload job for tracking. Returns the job ID."""
    job = create_job(
        supplier_id=current_user["id"],
        filename=filename,
        image_url=image_url,
        db=db,
    )
    return job.to_dict()
