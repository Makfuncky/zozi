"""AI upload job / staging product persistence (Law 2 thin-router helper).

Per ARCHITECTURE_DIAGRAM.md §3, all DB writes for supplier AI uploads are
centralized here so the router stays auth + require_feature + one call.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session


def _country_code(current_user) -> str:
    """Best-effort country_code resolution from the supplier context (Law 5)."""
    if current_user is None:
        return "OM"
    if isinstance(current_user, dict):
        return current_user.get("country_code") or current_user.get("cc") or "OM"
    return getattr(current_user, "country_code", None) or "OM"


def open_ai_job(
    db: Session,
    current_user,
    source_media_json: str,
    model_used: str = "stub",
) -> int:
    """Create an ``AIUploadJob`` row in 'pending' state and return its id."""
    from domains.catalog.ports import AIUploadJob

    supplier_id = (
        current_user.id
        if hasattr(current_user, "id")
        else int(current_user["sub"])
    )
    job = AIUploadJob(
        supplier_id=supplier_id,
        status="pending",
        model_used=model_used,
        source_media_json=source_media_json,
        country_code=_country_code(current_user),
    )
    db.add(job)
    db.flush()
    return job.id


def create_staging_row(
    db: Session,
    current_user,
    job_id: int,
    *,
    name: str,
    description: Optional[str],
    image_url: Optional[str],
    attributes: Optional[dict] = None,
    confidence: float = 0.0,
) -> int:
    """Create an ``AIStagingProduct`` row tied to the AIUploadJob."""
    from domains.catalog.ports import AIStagingProduct

    staging = AIStagingProduct(
        job_id=job_id,
        name=name,
        description=description,
        image_url=image_url,
        attributes=attributes or {},
        confidence_score=confidence,
        requires_human_review=True,
        country_code=_country_code(current_user),
    )
    db.add(staging)
    db.commit()
    db.refresh(staging)
    return staging.id