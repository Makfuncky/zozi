"""HR Dashboard router — onboarding pipeline, performance health, activity feed.
Also exposes a WebSocket endpoint for real-time activity push.
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from controllers.auth_controller import get_current_user
from data.db import get_db
from services.hr_dashboard_service import get_hr_dashboard as _svc_get_hr_dashboard
from utils.auth import decode_token as _decode_token
from utils.country_rls import enforce_country_access
from utils.datetime_utils import utcnow as _utcnow
from services.websocket_manager import ACTIVITY_ROOM
from services.websocket_manager import manager as ws_manager

logger = logging.getLogger(__name__)

router = APIRouter()


# ── WebSocket: Real-Time Activity Feed ─────────────────────────
@router.websocket("/ws/hr/activity")
async def websocket_hr_activity(websocket: WebSocket, token: str = Query(...)):
    """WebSocket endpoint for real-time HR activity feed.
    
    Clients connect with a JWT token. Events are broadcast to all
    connected clients whenever `log_activity()` is called.
    """
    # Authenticate
    payload = _decode_token(token)
    if payload is None:
        await websocket.close(code=4001, reason="Invalid token")
        return

    user_id = payload.get("user_id") or payload.get("sub")
    if not user_id:
        await websocket.close(code=4001, reason="Invalid user")
        return
    user_id = int(user_id)

    await ws_manager.connect(websocket, ACTIVITY_ROOM, user_id=user_id)
    await websocket.send_json({"type": "connected", "room": ACTIVITY_ROOM, "user_id": user_id})

    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, ACTIVITY_ROOM)
    except Exception as exc:
        logger.exception("HR Activity WebSocket error: %s", exc)
        ws_manager.disconnect(websocket, ACTIVITY_ROOM)


# ── REST Endpoints ──────────────────────────────────────────────


@router.get("/hr/dashboard")
def get_hr_dashboard(
    country_code: Optional[str] = Query(None, description="Filter by country code"),
    days: int = Query(7, ge=1, le=90, description="Recent activity window in days"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Return HR dashboard data: onboarding pipeline, performance health, activity feed."""
    return _svc_get_hr_dashboard(
        db,
        country_code=country_code,
        days=days,
        current_user=current_user,
    )
