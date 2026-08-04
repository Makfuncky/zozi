"""WebSocket endpoints for real-time chat, user notifications, and presence."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from data.db import get_db, get_db_session
from data.models_core import DirectChatRoom, DirectChatMessage, GroupChatRoom, GroupChatMessage, EntityChatThread, EntityChatMessage
from data.models import User, Notification, SupportTicket, TicketReply
from utils.config import settings
from services.core.users_write_service import get_user_by_id
from services.communication.chat_read_service import get_direct_chat_room_by_id, get_group_chat_room_by_id, get_entity_thread_by_id, get_room_messages, get_unread_direct_messages, get_unread_group_messages, get_unread_entity_messages
from services.communication.websocket_chat import persist_direct_message, persist_group_message, persist_entity_message, commit_read_receipts_messages

# Canonical user connection manager lives in services (single source of truth)
# â€” re-exported here for backward compatibility.
from services.websocket_manager import UserConnectionManager, user_manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])


def _decode_ws_token(token: str) -> Optional[dict]:
    """Decode JWT token for WebSocket authentication."""
    try:
        from utils.auth import SECRET_KEY, ALGORITHM
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception:
        return None


class ConnectionManager:
    """Manages WebSocket connections with presence, typing, and per-user tracking."""

    def __init__(self):
        self._rooms: dict[str, dict[int, set[WebSocket]]] = {}
        self._user_info: dict[int, dict] = {}
        self._typing: dict[str, set[int]] = {}

    async def connect(self, websocket: WebSocket, room_id: str, user_id: int, user_name: str = ""):
        await websocket.accept()
        (
            self._rooms.setdefault(room_id, {}).setdefault(user_id, set())
            |= {websocket}
        )
        self._user_info[user_id] = {
            "user_id": user_id,
            "name": user_name,
            "status": "online",
            "last_seen": datetime.now(timezone.utc).isoformat(),
            "rooms": set(),
        }
        self._user_info[user_id]["rooms"] |= {room_id}

    def disconnect(self, websocket: WebSocket, room_id: str, user_id: int):
        user_conns = self._rooms.get(room_id, {}).get(user_id, set())
        user_conns.discard(websocket)
        if not user_conns:
            self._rooms.get(room_id, {}).pop(user_id, None)
        if not self._rooms.get(room_id):
            self._rooms.pop(room_id, None)
        if user_id in self._user_info:
            self._user_info[user_id]["rooms"].discard(room_id)
            if not self._user_info[user_id]["rooms"]:
                self._user_info[user_id]["status"] = "offline"
                self._user_info[user_id]["last_seen"] = datetime.now(timezone.utc).isoformat()

    async def broadcast(self, room_id: str, message: dict, exclude_user_id: Optional[int] = None):
        dead = set()
        for uid, conns in self._rooms.get(room_id, {}).items():
            if uid == exclude_user_id:
                continue
            for ws in conns:
                try:
                    await ws.send_json(message)
                except Exception:
                    dead |= {ws}
        for ws in dead:
            for uid, conns in self._rooms.get(room_id, {}).items():
                conns.discard(ws)

    def set_typing(self, room_id: str, user_id: int, is_typing: bool):
        if is_typing:
            self._typing.setdefault(room_id, set()) |= {user_id}
        else:
            self._typing.get(room_id, set()).discard(user_id)
            if not self._typing.get(room_id):
                self._typing.pop(room_id, None)

    def get_typing_users(self, room_id: str) -> list[int]:
        return list(self._typing.get(room_id, set()))

    def get_room_users(self, room_id: str) -> list[dict]:
        users = []
        for uid in self._rooms.get(room_id, {}):
            info = self._user_info.get(uid, {})
            users.append({
                "user_id": uid,
                "name": info.get("name", f"User {uid}"),
                "status": info.get("status", "offline"),
                "last_seen": info.get("last_seen"),
            })
        return users

    def get_room_size(self, room_id: str) -> int:
        return len(self._rooms.get(room_id, {}))

    def get_user_status(self, user_id: int) -> Optional[dict]:
        info = self._user_info.get(user_id)
        if info:
            return {"user_id": user_id, "status": info.get("status", "offline"), "last_seen": info.get("last_seen")}
        return None


manager = ConnectionManager()


def _get_user_name(db: Session, user_id: int) -> str:
    user = get_user_by_id(db, user_id)
    if user:
        return user.full_name or user.name or user.email or f"User {user_id}"
    return f"User {user_id}"


def _persist_message(db: Session, room_id: str, sender_id: int, content: str, msg_type: str = "text"):
    """Store message in the database."""
    if room_id.startswith("dm_"):
        room = get_direct_chat_room_by_id(db, room_id)
        if room:
            msg = DirectChatMessage(room_id=room.id, sender_id=sender_id, message=content, message_type=msg_type)
            add_and_flush(db, msg)
            commit_and_refresh(db, msg)
            return msg.id, msg.created_at.isoformat()
    elif room_id.startswith("group_"):
        room = get_group_chat_room_by_id(db, room_id)
        if room:
            msg = GroupChatMessage(room_id=room.id, sender_id=sender_id, message=content, message_type=msg_type)
            add_and_flush(db, msg)
            commit_and_refresh(db, msg)
            return msg.id, msg.created_at.isoformat()
    else:
        thread = get_entity_thread_by_id(db, int(room_id))
        if thread:
            msg = EntityChatMessage(thread_id=thread.id, sender_id=sender_id, message=content)
            add_and_flush(db, msg)
            commit_and_refresh(db, msg)
            return msg.id, msg.created_at.isoformat()
    return None, None


def _mark_messages_read(db: Session, room_id: str, user_id: int):
    """Mark all messages from others in a room as read."""
    now = datetime.now(timezone.utc)
    count = 0
    if room_id.startswith("dm_"):
        room = get_direct_chat_room_by_id(db, room_id)
        if room:
            msgs = get_unread_direct_messages(db, room.id, user_id)
            for m in msgs:
                m.read_at = now
                count += 1
    elif room_id.startswith("group_"):
        room = get_group_chat_room_by_id(db, room_id)
        if room:
            msgs = get_unread_group_messages(db, room.id, user_id)
            for m in msgs:
                m.read_at = now
                count += 1
    else:
        msgs = get_unread_entity_messages(db, int(room_id), user_id)
        for m in msgs:
            m.read_at = now
            count += 1
    commit_only(db)
    return count


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


def _notification_payload(notification: Notification) -> dict:
    return {
        "type": "notification.created",
        "notification_id": int(notification.id),
        "notification_type": notification.type or "system",
        "title": notification.title,
        "message": notification.message,
        "link": getattr(notification, "link", None),
        "read": bool(notification.read_at),
        "created_at": notification.created_at.isoformat() if notification.created_at else None,
        "level": getattr(notification, "level", "info"),
    }


def _ticket_reply_payload(reply: TicketReply, ticket_id: int) -> dict:
    return {
        "type": "ticket.reply_created",
        "ticket_id": ticket_id,
        "reply_id": int(reply.id),
        "is_admin": bool(reply.is_admin),
        "title": "Support replied" if reply.is_admin else "New reply",
        "message": reply.message,
        "link": f"/tickets/{ticket_id}",
        "level": "info",
    }


def _admin_ticket_alert_payload(ticket: SupportTicket) -> dict:
    return {
        "type": "admin.alert.ticket",
        "ticket_id": int(ticket.id),
        "status": ticket.status,
        "level": "warning",
        "title": "Support ticket needs attention",
        "message": f"Ticket #{ticket.id} is open.",
        "link": "/admin/dashboard",
    }


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
        user = get_user_by_id(db, user_id)
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

