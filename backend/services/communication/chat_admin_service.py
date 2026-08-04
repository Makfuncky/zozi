"""Service methods for chat admin read operations."""
from sqlalchemy.orm import Session
from data.models_core import (
    ChatRoom,
    ChatMessage,
    DirectChatRoom,
    GroupChatRoom,
)


def get_all_chat_rooms(db: Session, skip: int = 0, limit: int = 20) -> list:
    """Get all chat rooms (direct and group)."""
    direct = db.query(DirectChatRoom).order_by(DirectChatRoom.created_at.desc()).offset(skip).limit(limit).all()
    group = db.query(GroupChatRoom).order_by(GroupChatRoom.created_at.desc()).offset(skip).limit(limit).all()
    return list(direct) + list(group)


def get_chat_room_by_id(db: Session, room_id: int) -> ChatRoom | None:
    """Get a chat room by ID (checks both types)."""
    room = db.query(DirectChatRoom).filter(DirectChatRoom.id == room_id).first()
    if room:
        return room
    return db.query(GroupChatRoom).filter(GroupChatRoom.id == room_id).first()


def get_chat_room_messages(db: Session, room_id: int, skip: int = 0, limit: int = 50) -> list:
    """Get messages for a chat room."""
    room = get_chat_room_by_id(db, room_id)
    if hasattr(room, 'chat_id'):
        return (
            db.query(ChatMessage)
            .filter(ChatMessage.room_id == room.id)
            .order_by(ChatMessage.created_at)
            .offset(skip)
            .limit(limit)
            .all()
        )
    return []


def get_chat_user_presence(db: Session, user_ids: list[int]) -> dict:
    """Get online presence for users."""
    from data.models import UserSession
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    presences = {}
    for uid in user_ids:
        session = (
            db.query(UserSession)
            .filter(UserSession.user_id == uid, UserSession.last_activity >= now.replace(hour=0))
            .first()
        )
        presences[uid] = session is not None
    return presences


def get_chat_metrics(db: Session) -> dict:
    """Get chat system metrics."""
    from sqlalchemy import func as sqlfunc
    total_rooms = db.query(
        sqlfunc.count(DirectChatRoom.id) + sqlfunc.count(GroupChatRoom.id)
    ).scalar() or 0
    total_messages = db.query(sqlfunc.count(ChatMessage.id)).scalar() or 0
    return {"total_rooms": total_rooms, "total_messages": total_messages}
