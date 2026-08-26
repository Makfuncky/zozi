from __future__ import annotations

from domains.customers.services.public_comms_status_service import ConnectionManager
from domains.customers.services.public_comms_status_service import UserConnectionManager
from domains.customers.services.public_comms_status_service import websocket_chat
from domains.customers.services.public_comms_status_service import _decode_ws_token

import json

import logging


from typing import Optional

from fastapi import WebSocket, WebSocketDisconnect, Depends, Query

from sqlalchemy.orm import Session

from jose import JWTError, jwt

from infrastructure.database.database import get_db, get_db_session

from infrastructure.utils.config import settings

from domains.comms.services.messaging.chat.chat_write_service import (
    get_user_display_name,
    get_user_role,
    persist_message,
    mark_messages_read,
)

logger = logging.getLogger(__name__)



manager = ConnectionManager()

def _get_user_name(db: Session, user_id: int) -> str:
    return get_user_display_name(db, user_id)

def _persist_message(db: Session, room_id: str, sender_id: int, content: str, msg_type: str = "text"):
    """Store message in the database (delegates to the chat write service)."""
    return persist_message(db, room_id, sender_id, content, msg_type)

def _mark_messages_read(db: Session, room_id: str, user_id: int):
    """Mark all messages from others in a room as read (delegates to service)."""
    return mark_messages_read(db, room_id, user_id)



user_manager = UserConnectionManager()

async def websocket_user(
    websocket: WebSocket,
    token: str = Query(...),
):
    payload = _decode_ws_token(token)
    if payload is None:
        await websocket.close(code=4001, reason="Invalid token")
        return

    user_id = payload.get("user_id") or payload.get("sub")
    if not user_id:
        await websocket.close(code=4001, reason="Invalid user")
        return

    user_id = int(user_id)

    db = next(get_db())
    try:
        role = get_user_role(db, user_id)
    finally:
        db.close()

    scope = "staff" if role in ("admin", "support", "country_head", "country_manager") else "user"
    if scope == "staff":
        await user_manager.connect_staff(websocket, user_id)
    else:
        await user_manager.connect_user(websocket, user_id)

    await websocket.send_json({"type": "connected", "scope": scope, "user_id": user_id})

    try:
        while True:
            data = await websocket.receive_json()
            event_type = data.get("type", "")
            if event_type == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        if scope == "staff":
            user_manager.disconnect_staff(websocket, user_id)
        else:
            user_manager.disconnect_user(websocket, user_id)

def get_online_users(room_id: str):
    """Get online users in a room with presence info."""
    return {"room_id": room_id, "online": manager.get_room_size(room_id), "users": manager.get_room_users(room_id)}

def get_user_status(user_id: int):
    """Get presence status for a specific user."""
    status = manager.get_user_status(user_id)
    if status:
        return status
    return {"user_id": user_id, "status": "offline", "last_seen": None}


