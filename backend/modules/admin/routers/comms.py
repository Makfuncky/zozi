from __future__ import annotations
import json
import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query, Path, Body, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from infrastructure.database.database import get_db
from infrastructure.security.dependencies import require_admin
from infrastructure.messaging.ws_manager import manager
from rbac.dependencies import require_feature
from domains.comms.services.email.email_management import EmailManagementService
from domains.comms.services.admin.communication_audit import get_communication_audit_service


"""Admin comms router — thin HTTP layer delegating to comms domain services."""





router = APIRouter(prefix="/api/v1/admin/comms", tags=["admin", "comms"])

USER_ROOM = "user:realtime"


@router.get("/campaigns")
def list_all_campaigns_route(
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=100),
    cursor: str | None = Query(None, description="Cursor for keyset pagination"),
):
    require_feature("comms.campaign.read")
    service = EmailManagementService(db)
    return service.list_all_campaigns(limit=limit)


@router.get("/metrics")
def admin_email_metrics_route(_: dict = Depends(require_admin), db: Session = Depends(get_db)):
    require_feature("comms.campaign.read")
    service = EmailManagementService(db)
    return service.get_email_metrics()


@router.get("/campaigns/{country_code}")
def list_campaigns_route(
    country_code: str = Path(..., description="ISO country code"),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=100),
    cursor: str | None = Query(None, description="Cursor for keyset pagination"),
):
    require_feature("comms.campaign.read")
    service = EmailManagementService(db)
    return service.get_campaigns_by_country(country_code, limit=limit)


@router.post("/campaigns/{country_code}", status_code=201)
def create_campaign_route(
    country_code: str = Path(..., description="ISO country code"),
    payload: dict = Body(...),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    require_feature("comms.campaign.create")
    service = EmailManagementService(db)
    return service.create_campaign(payload, country_code)


@router.delete("/campaigns/{country_code}/{campaign_id}")
def delete_campaign_route(
    country_code: str = Path(..., description="ISO country code"),
    campaign_id: int = Path(...),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    require_feature("comms.campaign.create")
    service = EmailManagementService(db)
    campaign = service.find_campaign_for_deletion(campaign_id, country_code)
    service.delete_campaign(campaign)
    return {"message": "Campaign deleted"}


# ── Communication audit (migrated from domains/audit/services/communication_audit) ──


@router.get("/audit", tags=["communication-audit"])
def get_communication_audit_trail_route(
    user_id: Optional[int] = Query(None),
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[int] = Query(None),
    action: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    require_feature("comms.audit.read")
    service = get_communication_audit_service(db)
    if service is None:
        return {"items": [], "total": 0, "limit": limit, "offset": offset}
    return service.get_audit_trail(
        user_id=user_id,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        limit=limit,
        offset=offset,
    )


@router.get("/audit/export", tags=["communication-audit"])
def export_communication_audit_for_ediscovery_route(
    user_id: Optional[int] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    require_feature("audit.logs.export")
    service = get_communication_audit_service(db)
    if service is None:
        return {"exported": 0, "format": "json"}
    return service.export_for_ediscovery(
        user_id=user_id,
        date_from=date_from,
        date_to=date_to,
    )


# ── User realtime WebSocket (moved from modules/admin/routers/public_comms_status.py) ──

logger = logging.getLogger(__name__)


async def websocket_user(websocket: WebSocket):
    """Handle a user realtime WebSocket connection."""
    await websocket.accept()
    manager.active_connections[USER_ROOM].append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
            except json.JSONDecodeError:
                payload = {"raw": data}
            await manager.broadcast_to_room(USER_ROOM, payload)
    except WebSocketDisconnect:
        pass
    except Exception:
        logger.debug("websocket_user connection closed unexpectedly")
    finally:
        if websocket in manager.active_connections[USER_ROOM]:
            manager.active_connections[USER_ROOM].remove(websocket)
