"""Real-time chat persistence helpers for the WebSocket comms router.

These were previously inlined in ``routers/public_comms_status.py``. They are
called from inside WebSocket handlers with a manually-managed session
(``get_db_session()``), so the router passes the session in and this module
owns the actual ``db.query`` / ``add`` / ``commit`` work.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from models.core import (
    DirectChatRoom,
    DirectChatMessage,
    GroupChatRoom,
    GroupChatMessage,
    EntityChatThread,
    EntityChatMessage,
)
from models import User


def get_user_name(db: Session, user_id: int) -> str:
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        return user.full_name or user.name or user.email or f"User {user_id}"
    return f"User {user_id}"


def get_user_role(db: Session, user_id: int) -> str:
    user = db.query(User).filter(User.id == user_id).first()
    return user.role if user else ""


def persist_message(db: Session, room_id: str, sender_id: int, content: str, msg_type: str = "text"):
    """Store message in the database. Returns ``(message_id, created_at_iso)``."""
    if room_id.startswith("dm_"):
        room = db.query(DirectChatRoom).filter(DirectChatRoom.chat_id == room_id).first()
        if room:
            msg = DirectChatMessage(room_id=room.id, sender_id=sender_id, message=content, message_type=msg_type)
            db.add(msg)
            db.commit()
            db.refresh(msg)
            return msg.id, msg.created_at.isoformat()
    elif room_id.startswith("group_"):
        room = db.query(GroupChatRoom).filter(GroupChatRoom.chat_id == room_id).first()
        if room:
            msg = GroupChatMessage(room_id=room.id, sender_id=sender_id, message=content, message_type=msg_type)
            db.add(msg)
            db.commit()
            db.refresh(msg)
            return msg.id, msg.created_at.isoformat()
    else:
        thread = db.query(EntityChatThread).filter(EntityChatThread.id == int(room_id)).first()
        if thread:
            msg = EntityChatMessage(thread_id=thread.id, sender_id=sender_id, message=content)
            db.add(msg)
            db.commit()
            db.refresh(msg)
            return msg.id, msg.created_at.isoformat()
    return None, None


def mark_messages_read(db: Session, room_id: str, user_id: int) -> int:
    """Mark all messages from others in a room as read. Returns count updated."""
    now = datetime.now(timezone.utc)
    count = 0
    if room_id.startswith("dm_"):
        room = db.query(DirectChatRoom).filter(DirectChatRoom.chat_id == room_id).first()
        if room:
            msgs = db.query(DirectChatMessage).filter(
                DirectChatMessage.room_id == room.id,
                DirectChatMessage.sender_id != user_id,
                DirectChatMessage.read_at.is_(None),
            ).all()
            for m in msgs:
                m.read_at = now
                count += 1
    elif room_id.startswith("group_"):
        room = db.query(GroupChatRoom).filter(GroupChatRoom.chat_id == room_id).first()
        if room:
            msgs = db.query(GroupChatMessage).filter(
                GroupChatMessage.room_id == room.id,
                GroupChatMessage.sender_id != user_id,
                GroupChatMessage.read_at.is_(None),
            ).all()
            for m in msgs:
                m.read_at = now
                count += 1
    else:
        msgs = db.query(EntityChatMessage).filter(
            EntityChatMessage.thread_id == int(room_id),
            EntityChatMessage.sender_id != user_id,
            EntityChatMessage.read_at.is_(None),
        ).all()
        for m in msgs:
            m.read_at = now
            count += 1
    db.commit()
    return count
