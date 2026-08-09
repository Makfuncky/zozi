"""Thin controller for the AI upload pipeline (W1 remediation).

Keeps request-shaped orchestration (identity extraction, delegation) out of the
router while owning **no** DB mutations: every write is delegated to
``services.ai.ai_upload_write_service``, which owns the transaction boundary.
``HTTPException``s raised by the service propagate untouched.
"""
from __future__ import annotations

from typing import Any, Optional

from fastapi import UploadFile
from sqlalchemy.orm import Session

from services.ai.ai_upload_write_service import (
    cancel_ai_upload_job as _cancel_ai_upload_job,
)
from services.ai.ai_upload_write_service import (
    create_ai_upload_job as _create_ai_upload_job,
)
from services.ai.ai_upload_write_service import (
    process_ai_upload_job as _process_ai_upload_job,
)
from services.ai.ai_upload_write_service import (
    publish_ai_upload_job as _publish_ai_upload_job,
)
import structlog
logger = structlog.get_logger(__name__)


def _resolve_user_id(current_user: dict) -> Any:
    """Extract the acting supplier/admin id from the auth payload."""
    user_id = current_user.get("id") or current_user.get("user_id")
    if user_id is None and isinstance(current_user.get("user"), dict):
        user_id = current_user["user"].get("id")
    return user_id


def create_job(
    images: list[UploadFile],
    country_code: str,
    model_used: Optional[str],
    prompt_hash: Optional[str],
    current_user: dict,
    db: Session,
) -> dict[str, Any]:
    return _create_ai_upload_job(
        db,
        supplier_id=_resolve_user_id(current_user),
        country_code=country_code,
        images=images,
        model_used=model_used,
        prompt_hash=prompt_hash,
    )


def publish_job(
    job_id: int,
    overrides: Optional[dict],
    current_user: dict,
    db: Session,
) -> dict[str, Any]:
    return _publish_ai_upload_job(db, job_id, overrides)


def cancel_job(job_id: int, current_user: dict, db: Session) -> dict[str, Any]:
    return _cancel_ai_upload_job(db, job_id)


def process_job(job_id: int) -> None:
    """Background-task entrypoint; the service opens/owns its own session."""
    return _process_ai_upload_job(job_id)
