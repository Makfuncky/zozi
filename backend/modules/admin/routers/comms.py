from __future__ import annotations
import json
import logging
import uuid
from datetime import datetime
from typing import Optional
from fastapi import (
    APIRouter,
    Body,
    Depends,
    HTTPException,
    Path,
    Query,
    WebSocket,
    WebSocketDisconnect,
)
from sqlalchemy.orm import Session
from infrastructure.database.database import get_db
from infrastructure.security.dependencies import require_admin
from infrastructure.messaging.ws_manager import manager
from rbac.dependencies import require_feature
from domains.comms.services.email.email_management import EmailManagementService
from domains.comms.services.admin import get_communication_audit_service


"""Admin comms router — thin HTTP layer delegating to comms domain services."""





router = APIRouter(prefix="/api/v1/admin/comms", tags=["admin", "comms"])

USER_ROOM = "user:realtime"


@router.get("/campaigns")
def list_all_campaigns_route(
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=100),
    cursor: str | None = Query(None, description="Cursor for keyset pagination"),
    _rf_gate: None = Depends(require_feature("comms.campaign.read")),
):
    service = EmailManagementService(db)
    return service.list_all_campaigns(limit=limit)


@router.get("/metrics")
def admin_email_metrics_route(_: dict = Depends(require_admin), db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("comms.campaign.read"))
):
    service = EmailManagementService(db)
    return service.get_email_metrics()


@router.get("/campaigns/{country_code}")
def list_campaigns_route(
    country_code: str = Path(..., description="ISO country code"),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=100),
    cursor: str | None = Query(None, description="Cursor for keyset pagination"),
    _rf_gate: None = Depends(require_feature("comms.campaign.read")),
):
    service = EmailManagementService(db)
    return service.get_campaigns_by_country(country_code, limit=limit)


@router.post("/campaigns/{country_code}", status_code=201)
def create_campaign_route(
    country_code: str = Path(..., description="ISO country code"),
    payload: dict = Body(...),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("comms.campaign.create")),
):
    service = EmailManagementService(db)
    return service.create_campaign(payload, country_code)


@router.delete("/campaigns/{country_code}/{campaign_id}")
def delete_campaign_route(
    country_code: str = Path(..., description="ISO country code"),
    campaign_id: int = Path(...),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("comms.campaign.create")),
):
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
    _rf_gate: None = Depends(require_feature("comms.audit.read")),
):
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
    _rf_gate: None = Depends(require_feature("audit.logs.export")),
):
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


async def websocket_user(websocket: WebSocket, token: str | None = None):
    """Handle a user realtime WebSocket connection.

    Law 41: the socket is authenticated with a JWT ``?token=`` query param
    using ``expected_type="access"`` so a refresh token cannot open it. The
    socket is bound to a per-user room rather than the shared ``USER_ROOM``
    so one user can never receive another user's realtime traffic.
    """
    from infrastructure.utils.auth import decode_token

    # Law 92/93: a WebSocket upgrade never traverses the HTTP middleware
    # pipeline, so the correlation id is taken from the handshake header when
    # the client sent one and minted here otherwise. Law 282: the token is a
    # credential, so neither it nor the raw query string is ever logged.
    peer = websocket.client
    peer_info = f"{peer.host}:{peer.port}" if peer is not None else "unknown"
    request_id = websocket.headers.get("x-request-id") or str(uuid.uuid4())
    log_ctx = {"peer": peer_info, "request_id": request_id}

    if not token:
        logger.warning("websocket_user rejected: missing token", extra=log_ctx)
        await websocket.close(code=4001, reason="Missing token")
        return
    try:
        payload = decode_token(token, expected_type="access")
    except HTTPException as exc:
        # Law 33/43: a rejected credential is a security event -> WARNING+.
        # Law 282: the reason is logged, never the token.
        logger.warning(
            "websocket_user rejected: token verification failed (%s)",
            exc.detail,
            extra=log_ctx,
        )
        await websocket.close(code=4001, reason="Invalid token")
        return

    user_id = payload.get("sub")
    if not user_id:
        logger.warning("websocket_user rejected: token has no subject", extra=log_ctx)
        await websocket.close(code=4001, reason="Invalid token payload")
        return

    room = f"{USER_ROOM}:{user_id}"

    await websocket.accept()
    await manager.connect(websocket, room, user_id=int(user_id) if str(user_id).isdigit() else None)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                payload_in = json.loads(data)
            except json.JSONDecodeError:
                payload_in = {"raw": data}
            # Echo back only to the authenticated user's own room.
            await manager.broadcast_to_room(room, payload_in)
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        # Law 59: the exception is logged, not swallowed. Law 43: an aborted
        # realtime session is a security-relevant event, so it is reported at
        # WARNING+ with the peer and request_id rather than at DEBUG.
        logger.warning(
            "websocket_user connection aborted: %s",
            type(exc).__name__,
            exc_info=True,
            extra=log_ctx,
        )
    finally:
        manager.disconnect(websocket, room)
