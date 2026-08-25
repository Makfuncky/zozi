"""Admin governance router — canonical."""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status

from __future__ import annotations
from datetime import datetime, timezone
from domains.comms.models.communication import Notification
from domains.governance.models.admin import TicketReply
from domains.governance.models.core import DirectChatMessage
from domains.governance.models.core import DirectChatRoom
from domains.governance.models.core import EntityChatMessage
from domains.governance.models.core import EntityChatThread
from domains.governance.models.core import GroupChatMessage
from domains.governance.models.core import GroupChatRoom
from domains.governance.models.core import SupportTicket
from domains.governance.models.user import User
from infrastructure.database.database import get_db
from infrastructure.database.database import get_db, get_db_session
from infrastructure.utils.auth import SECRET_KEY, ALGORITHM
from infrastructure.utils.config import settings
from infrastructure.utils.dependencies import require_admin
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from typing import Optional
import json
import logging

router = APIRouter(prefix="/api/v1/admin/governance", tags=["admin", "governance"])

@router.get("/config/checkout")
def get_checkout_config():
    """
    Public checkout configuration endpoint.
    Returns VAT rate, shipping flat rate, and free shipping threshold.
    """
    return {
        "vat_rate": 0.05,
        "shipping_flat_rate": 2.0,
        "free_shipping_threshold": 0.0,
    }


@router.websocket("/ws/chat/{room_id}")
async def websocket_chat(
    websocket: WebSocket,
    room_id: str,
    token: str = Query(...),
):
    """Real-time chat WebSocket with presence, typing, and read receipts.

    Query params:
    - token: JWT authentication token
    """
    payload = _decode_ws_token(token)
    if payload is None:
        await websocket.close(code=4001, reason="Invalid token")
        return

    user_id = payload.get("user_id") or payload.get("sub")
    if not user_id:
        await websocket.close(code=4001, reason="Invalid user")
        return

    user_id = int(user_id)

    db = get_db_session()
    try:
        user_name = _get_user_name(db, user_id)
    finally:
        db.close()

    await manager.connect(websocket, room_id, user_id, user_name)

    # Notify others in the room about the new user
    room_users = manager.get_room_users(room_id)
    await manager.broadcast(room_id, {
        "type": "user_joined",
        "room_id": room_id,
        "user_id": user_id,
        "user_name": user_name,
        "users": room_users,
    })

    try:
        while True:
            data = await websocket.receive_json()
            event_type = data.get("type", "message")

            if event_type == "message":
                content = data.get("content", "")
                msg_type = data.get("message_type", "text")
                if not content:
                    continue

                db = get_db_session()
                try:
                    msg_id, created_at = _persist_message(db, room_id, user_id, content, msg_type)
                finally:
                    db.close()

                await manager.broadcast(room_id, {
                    "type": "message",
                    "room_id": room_id,
                    "sender_id": user_id,
                    "sender_name": user_name,
                    "content": content,
                    "message_type": msg_type,
                    "message_id": msg_id,
                    "created_at": created_at,
                })

            elif event_type == "typing":
                is_typing = data.get("is_typing", False)
                manager.set_typing(room_id, user_id, is_typing)

                typing_users = manager.get_typing_users(room_id)
                typing_names = []
                for tuid in typing_users:
                    uinfo = manager._user_info.get(tuid, {})
                    typing_names.append(uinfo.get("name", f"User {tuid}"))

                await manager.broadcast(room_id, {
                    "type": "typing",
                    "room_id": room_id,
                    "user_id": user_id,
                    "user_name": user_name,
                    "is_typing": is_typing,
                    "typing_user_ids": typing_users,
                    "typing_user_names": typing_names,
                }, exclude_user_id=user_id)

            elif event_type == "read_receipt":
                db = get_db_session()
                try:
                    count = _mark_messages_read(db, room_id, user_id)
                finally:
                    db.close()

                await manager.broadcast(room_id, {
                    "type": "read_receipt",
                    "room_id": room_id,
                    "user_id": user_id,
                    "user_name": user_name,
                    "count": count,
                }, exclude_user_id=user_id)

            elif event_type == "presence":
                status = data.get("status", "online")
                if user_id in manager._user_info:
                    manager._user_info[user_id]["status"] = status
                user_rooms = list(manager._user_info.get(user_id, {}).get("rooms", set()))
                for rid in user_rooms:
                    await manager.broadcast(rid, {
                        "type": "presence",
                        "room_id": rid,
                        "user_id": user_id,
                        "user_name": user_name,
                        "status": status,
                        "users": manager.get_room_users(rid),
                    }, exclude_user_id=user_id)

            elif event_type == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id, user_id)
        room_users = manager.get_room_users(room_id)
        await manager.broadcast(room_id, {
            "type": "user_left",
            "room_id": room_id,
            "user_id": user_id,
            "user_name": user_name,
            "users": room_users,
        })
    except Exception as exc:
        logger.exception("WebSocket error: %s", exc)
        manager.disconnect(websocket, room_id, user_id)


class UserConnectionManager:
    """Manages per-user WebSocket connections for notifications and alerts."""

    def __init__(self):
        self._user_sockets: dict[int, set[WebSocket]] = {}
        self._staff_sockets: dict[int, set[WebSocket]] = {}

    async def connect_user(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self._user_sockets.setdefault(user_id, set()).add(websocket)

    async def connect_staff(self, websocket: WebSocket, staff_id: int):
        await websocket.accept()
        self._staff_sockets.setdefault(staff_id, set()).add(websocket)

    def disconnect_user(self, websocket: WebSocket, user_id: int):
        conns = self._user_sockets.get(user_id, set())
        conns.discard(websocket)
        if not conns:
            self._user_sockets.pop(user_id, None)

    def disconnect_staff(self, websocket: WebSocket, staff_id: int):
        conns = self._staff_sockets.get(staff_id, set())
        conns.discard(websocket)
        if not conns:
            self._staff_sockets.pop(staff_id, None)

    async def broadcast_to_user(self, user_id: int, message: dict):
        dead = set()
        for ws in self._user_sockets.get(user_id, set()):
            try:
                await ws.send_json(message)
            except Exception:
                dead.add(ws)
        for ws in dead:
            self._user_sockets.get(user_id, set()).discard(ws)

    async def broadcast_to_staff(self, staff_id: int, message: dict):
        dead = set()
        for ws in self._staff_sockets.get(staff_id, set()):
            try:
                await ws.send_json(message)
            except Exception:
                dead.add(ws)
        for ws in dead:
            self._staff_sockets.get(staff_id, set()).discard(ws)

    async def broadcast_to_all_staff(self, message: dict):
        for staff_id in list(self._staff_sockets.keys()):
            await self.broadcast_to_staff(staff_id, message)



@router.websocket("/ws/user")
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
        user = db.query(User).filter(User.id == user_id).first()
        role = user.role if user else ""
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


@router.get("/ws/room/{room_id}/online")
def get_online_users(room_id: str):
    """Get online users in a room with presence info."""
    return {"room_id": room_id, "online": manager.get_room_size(room_id), "users": manager.get_room_users(room_id)}



@router.get("/ws/user/{user_id}/status")
def get_user_status(user_id: int):
    """Get presence status for a specific user."""
    status = manager.get_user_status(user_id)
    if status:
        return status
    return {"user_id": user_id, "status": "offline", "last_seen": None}


