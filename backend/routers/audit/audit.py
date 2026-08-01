import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from db.database import get_db
from services.communication_audit import get_communication_audit_service

logger = logging.getLogger("zozi.api.audit")
router = APIRouter()


@router.get("/audit")
def get_audit_trail(
    user_id: Optional[int] = Query(None),
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[int] = Query(None),
    action: Optional[str] = Query(None),
    limit: int = Query(100),
    offset: int = Query(0),
    db: Session = Depends(get_db),
):
    service = get_communication_audit_service(db)
    return service.get_audit_trail(
        user_id=user_id,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        limit=limit,
        offset=offset,
    )


@router.get("/audit/export")
def export_for_ediscovery(
    user_id: Optional[int] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
):
    service = get_communication_audit_service(db)
    return service.export_for_ediscovery(
        user_id=user_id,
        date_from=date_from,
        date_to=date_to,
    )
