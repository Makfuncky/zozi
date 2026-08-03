"""
eDiscovery API Router
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from services.audit.ediscovery import get_ediscovery_service, EDiscoveryService
from data.db import get_db
from data.dependencies_auth import get_current_user
from data.controllers_admin_controller import require_admin

router = APIRouter()


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
    db: Session = Depends(get_db)
):
    service = get_ediscovery_service(db)
    return service.search_audit_trail(
        entity_type=entity_type,
        entity_id=entity_id,
        user_id=user_id,
        action=action,
        start_date=start_date,
        end_date=end_date,
        limit=limit
    )


@router.get("/timeline/{entity_type}/{entity_id}")
async def get_entity_timeline(
    entity_type: str,
    entity_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    service = get_ediscovery_service(db)
    return service.get_entity_timeline(entity_type, entity_id)


@router.get("/export/{entity_type}/{entity_id}")
async def export_for_legal(
    entity_type: str,
    entity_id: int,
    format: str = Query("json"),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    service = get_ediscovery_service(db)
    return service.export_for_legal(entity_type, entity_id, format)
