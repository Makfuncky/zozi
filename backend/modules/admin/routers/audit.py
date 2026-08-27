from __future__ import annotations
from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.orm import Session
from typing import Optional
from infrastructure.database.database import get_db
from infrastructure.security.dependencies import require_admin
from rbac.dependencies import require_feature
from domains.audit.services.ediscovery import get_ediscovery_service



"""Admin audit router — canonical."""



router = APIRouter(prefix="/api/v1/admin/audit", tags=["admin", "audit"])


@router.get("/search")
async def search_audit_trail(
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[int] = Query(None),
    user_id: Optional[int] = Query(None),
    action: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    service = get_ediscovery_service(db)
    require_feature("audit.read")
    return service.search_audit_trail(
        entity_type=entity_type,
        entity_id=entity_id,
        user_id=user_id,
        action=action,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )


@router.get("/timeline/{entity_type}/{entity_id}")
async def get_entity_timeline(
    entity_type: str,
    entity_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    service = get_ediscovery_service(db)
    require_feature("audit.read")
    return service.get_entity_timeline(entity_type, entity_id)


@router.get("/export/{entity_type}/{entity_id}")
async def export_for_legal(
    entity_type: str,
    entity_id: int,
    format: str = Query("json"),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    service = get_ediscovery_service(db)
    require_feature("audit.logs.export")
    return service.export_for_legal(entity_type, entity_id, format)
