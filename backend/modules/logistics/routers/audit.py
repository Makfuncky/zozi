"""Logistics audit router — logistics-partner-facing self-service audit endpoints.

Logistics partners may view their own audit trail (shipments, pickups, login history).
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from infrastructure.database.database import get_db
from rbac.dependencies import get_current_user
from rbac.dependencies import require_feature
from domains.audit.services.ediscovery import get_ediscovery_service
from domains.audit.services.logs.audit_query_service import get_audit_logs

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/logistics/audit", tags=["logistics", "audit"])


class LogisticsActivityEntry(BaseModel):
    id: int
    action: str
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    ip_address: Optional[str] = None
    created_at: Optional[str] = None


class LogisticsAuditTrail(BaseModel):
    items: list
    total: int
    page: int
    page_size: int
    total_pages: int


@router.get("/my-activity", response_model=LogisticsAuditTrail)
def my_audit_activity(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    action: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    __: None = Depends(require_feature("audit.read")),
):
    """Return the authenticated logistics partner's own audit trail."""
    try:
        user_id = current_user.get("id") if isinstance(current_user, dict) else getattr(current_user, "id", None)
        if not user_id:
            raise HTTPException(status_code=401, detail="Not authenticated")

        return get_audit_logs(
            db,
            page=page,
            page_size=page_size,
            user_id_filter=int(user_id),
            action_filter=action,
            start_date=start_date,
            end_date=end_date,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error fetching logistics audit activity: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/my-timeline")
def my_recent_timeline(
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    __: None = Depends(require_feature("audit.read")),
):
    """Return the logistics partner's most recent activity for the dashboard widget."""
    try:
        user_id = current_user.get("id") if isinstance(current_user, dict) else getattr(current_user, "id", None)
        if not user_id:
            raise HTTPException(status_code=401, detail="Not authenticated")

        service = get_ediscovery_service(db)
        records = service.search_audit_trail(user_id=int(user_id), limit=limit)
        return {"items": records, "count": len(records)}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error fetching logistics timeline: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error")
