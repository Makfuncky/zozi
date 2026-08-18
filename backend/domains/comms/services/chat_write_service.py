"""Chat write service.

Owns the DB writes for WebSocket chat persistence (message storage and read
receipts). Functions receive the active SQLAlchemy ``Session`` from the caller
so no session is opened or closed here — keeps the router circuit clean (W1)
while staying testable.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from domains.accounts.models.core import DirectChatMessage
from domains.accounts.models.core import DirectChatRoom
from domains.accounts.models.core import EntityChatMessage
from domains.accounts.models.core import EntityChatThread
from domains.accounts.models.core import GroupChatMessage
from domains.accounts.models.core import GroupChatRoom
import structlog
logger = structlog.get_logger(__name__)


def persist_message(
    db: Session,
    room_id: str,
    sender_id: int,
    content: str,
    msg_type: str = "text",
) -> Tuple[Optional[int], Optional[str]]:
    """Store a chat message for the given room and return (id, created_at_iso)."""
    if room_id.startswith("dm_"):
        room = db.query(DirectChatRoom).filter(DirectChatRoom.chat_id == room_id).first()
        if room:
            msg = DirectChatMessage(
                room_id=room.id, sender_id=sender_id, message=content, message_type=msg_type
            )
            db.add(msg)
            db.commit()
            db.refresh(msg)
            return msg.id, msg.created_at.isoformat()
    elif room_id.startswith("group_"):
        room = db.query(GroupChatRoom).filter(GroupChatRoom.chat_id == room_id).first()
        if room:
            msg = GroupChatMessage(
                room_id=room.id, sender_id=sender_id, message=content, message_type=msg_type
            )
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
    """Mark all unread messages from others in the room as read; return count."""
    now = datetime.now(timezone.utc)
    count = 0
    if room_id.startswith("dm_"):
        room = db.query(DirectChatRoom).filter(DirectChatRoom.chat_id == room_id).first()
        if room:
            msgs = (
                db.query(DirectChatMessage)
                .filter(
                    DirectChatMessage.room_id == room.id,
                    DirectChatMessage.sender_id != user_id,
                    DirectChatMessage.read_at.is_(None),
                )
                .all()
            )
            for m in msgs:
                m.read_at = now
                count += 1
    elif room_id.startswith("group_"):
        room = db.query(GroupChatRoom).filter(GroupChatRoom.chat_id == room_id).first()
        if room:
            msgs = (
                db.query(GroupChatMessage)
                .filter(
                    GroupChatMessage.room_id == room.id,
                    GroupChatMessage.sender_id != user_id,
                    GroupChatMessage.read_at.is_(None),
                )
                .all()
            )
            for m in msgs:
                m.read_at = now
                count += 1
    else:
        msgs = (
            db.query(EntityChatMessage)
            .filter(
                EntityChatMessage.thread_id == int(room_id),
                EntityChatMessage.sender_id != user_id,
                EntityChatMessage.read_at.is_(None),
            )
            .all()
        )
        for m in msgs:
            m.read_at = now
            count += 1
    db.commit()
    return count
