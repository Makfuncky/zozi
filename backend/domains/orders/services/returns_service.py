"""Returns service — owns return-request write orchestration for the returns module.

Layering contract (ARCHITECTURE_DIAGRAM.md §10):
    routers -> controllers -> services (this module) -> models

The single write previously inlined in ``routers.public_returns_access.update_return_status``
(``db.query`` + ``db.commit``) now lives here so the router stays a thin,
read-only orchestration surface (fixes the W1 violation at the router boundary).

NOTE: ``controllers.orders.returns_controller`` still performs write operations for the
other return endpoints. Those are being migrated into this service incrementally;
this module owns the status-update write as the first extracted operation.
"""
from __future__ import annotations

from typing import Any, Dict

from fastapi import HTTPException
from sqlalchemy.orm import Session

from _legacy.models import ReturnRequest
import structlog
logger = structlog.get_logger(__name__)


def update_return_request_status(
    return_id: int, status: str, notes: str | None, db: Session
) -> Dict[str, Any]:
    """Update a return request's status and optional resolution notes.

    Returns a small message envelope. Raises 404 if the request is missing.
    """
    r = db.query(ReturnRequest).filter(ReturnRequest.id == return_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Return request not found")
    r.status = status
    if notes:
        r.resolution_notes = notes
    db.commit()
    return {"message": "Updated"}
