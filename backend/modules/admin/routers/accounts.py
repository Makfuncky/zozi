"""Admin accounts router — canonical."""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status

from .identity import router as identity_router
from .sessions import router as sessions_router
from __future__ import annotations
from modules.admin.routers.accounts import delete_bank_account_route, list_pending_bank_accounts_route, verify_bank_account_route
from domains.accounts.services.users.users_admin_service import get_user_display_name
from domains.accounts.services.users.users_admin_service import get_user_role
from domains.comms.services._auto_stubs import mark_messages_read
from domains.comms.services._auto_stubs import persist_message
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
import logging as _l; _l.getLogger(__name__).warning("skip accounts_router: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip identity_router: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip sessions_router: %s", _e)

router = APIRouter(prefix="/api/v1/admin/accounts", tags=["admin", "accounts"])

@router.get("/bank-accounts/{country_code}/pending", status_code=200, tags=['admin-bank-accounts'])
def list_pending_bank_accounts_route_route(
    country_code: str,
    kind: str = Query('supplier'),
    page: int = Query(1),
    page_size: int = Query(50),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)


@router.post("/bank-accounts/{country_code}/{kind}/{account_id}/verify", status_code=201, tags=['admin-bank-accounts'])
def verify_bank_account_route_route(
    country_code: str,
    kind: str,
    account_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    action: str = Body('approve', embed=True),
    note: Optional[str] = Body(None, embed=True)


@router.delete("/bank-accounts/{country_code}/{kind}/{account_id}", status_code=200, tags=['admin-bank-accounts'])
def delete_bank_account_route_route(
    country_code: str,
    kind: str,
    account_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)


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



