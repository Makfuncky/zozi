from __future__ import annotations

import logging
from typing import Optional

from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from infrastructure.database.database import get_db
from domains.hr.services.coi_service import COIService

logger = logging.getLogger(__name__)


def coi_check_dependency(
    request: Request,
    db: Session = None,
):
    """FastAPI dependency to check for COI before processing.

    Lives in the dependencies layer (which is permitted to reach services),
    keeping the middleware layer free of service/model imports.
    """
    if db is None:
        with get_db() as db_session:
            return _coi_check_internal(request, db_session)
    return _coi_check_internal(request, db)


def _coi_check_internal(request: Request, db: Session):
    """Internal COI check implementation."""
    user = getattr(request.state, "user", None)
    if not user:
        return None

    coi_service = COIService(db)

    entity_id = request.path_params.get("supplier_id") or request.path_params.get("logistics_partner_id")
    entity_type = "supplier" if "supplier" in request.url.path else "logistics_partner"

    if entity_id:
        uid = user["id"] if isinstance(user, dict) else getattr(user, "id", None)
        coi_result = coi_service.detect_coi(uid, int(entity_id), entity_type)
        if coi_result and coi_result.get("requires_approval"):
            raise HTTPException(
                status_code=409,
                detail="Conflict of interest detected - requires senior approval",
            )
    return None

