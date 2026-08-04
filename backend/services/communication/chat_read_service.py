"""Service methods for WebSocket chat data access."""
from __future__ import annotations
from sqlalchemy.orm import Session
from data.models import User
from data.models_core import DirectChatRoom, GroupChatRoom, EntityChatThread, EntityChatMessage, DirectChatMessage, GroupChatMessage
from data.models_communication import GroupChatMember


def get_direct_chat_room_by_id(db: Session, chat_id: str) -> DirectChatRoom | None:
    """Get a direct chat room by its chat_id."""
    return db.query(DirectChatRoom).filter(DirectChatRoom.chat_id == chat_id).first()


def get_group_chat_room_by_id(db: Session, chat_id: str) -> GroupChatRoom | None:
    """Get a group chat room by its chat_id."""
    return db.query(GroupChatRoom).filter(GroupChatRoom.chat_id == chat_id).first()


def get_entity_thread_by_id(db: Session, thread_id: int) -> EntityChatThread | None:
    """Get an entity chat thread by ID."""
    return db.query(EntityChatThread).filter(EntityChatThread.id == thread_id).first()


def get_room_messages(db: Session, room_type: str, room_id: str, skip: int = 0, limit: int = 50) -> list:
    """Get messages for a chat room."""
    if room_type == "direct":
        room = get_direct_chat_room_by_id(db, room_id)
        if room:
            return (
                db.query(DirectChatMessage)
                .filter(DirectChatMessage.room_id == room.id)
                .order_by(DirectChatMessage.created_at)
                .offset(skip)
                .limit(limit)
                .all()
            )
    elif room_type == "group":
        room = get_group_chat_room_by_id(db, room_id)
        if room:
            return (
                db.query(GroupChatMessage)
                .filter(GroupChatMessage.room_id == room.id)
                .order_by(GroupChatMessage.created_at)
                .offset(skip)
                .limit(limit)
                .all()
            )
    elif room_type == "entity":
        thread = get_entity_thread_by_id(db, room_id)
        if thread:
            return (
                db.query(EntityChatMessage)
                .filter(EntityChatMessage.thread_id == thread.id)
                .order_by(EntityChatMessage.created_at)
                .offset(skip)
                .limit(limit)
                .all()
            )
    return []


def get_direct_room_participant_count(db: Session, room_id: int) -> int:
    """Count participants in a direct chat room.

    DirectChatRoom stores its two participants as ``participant_one`` and
    ``participant_two`` columns (no join table exists).
    """
    room = db.query(DirectChatRoom).filter(DirectChatRoom.id == room_id).first()
    if not room:
        return 0
    return 2 if room.participant_two is not None else 1


def get_group_room_participant_count(db: Session, room_id: int) -> int:
    """Count participants in a group chat room via the GroupChatMember join model."""
    return (
        db.query(GroupChatMember)
        .filter(GroupChatMember.room_id == room_id)
        .count()
    )


def get_user_by_id(db: Session, user_id: int) -> User | None:
    """Get user by ID."""
    return db.query(User).filter(User.id == user_id).first()


def get_unread_direct_messages(db: Session, room_id: int, user_id: int) -> list[DirectChatMessage]:
    """Get unread direct chat messages from other senders in a room."""
    return (
        db.query(DirectChatMessage)
        .filter(
            DirectChatMessage.room_id == room_id,
            DirectChatMessage.sender_id != user_id,
            DirectChatMessage.read_at.is_(None),
        )
        .all()
    )


def get_unread_group_messages(db: Session, room_id: int, user_id: int) -> list[GroupChatMessage]:
    """Get unread group chat messages from other senders in a room."""
    return (
        db.query(GroupChatMessage)
        .filter(
            GroupChatMessage.room_id == room_id,
            GroupChatMessage.sender_id != user_id,
            GroupChatMessage.read_at.is_(None),
        )
        .all()
    )


def get_unread_entity_messages(db: Session, thread_id: int, user_id: int) -> list[EntityChatMessage]:
    """Get unread entity chat messages from other senders in a thread."""
    return (
        db.query(EntityChatMessage)
        .filter(
            EntityChatMessage.thread_id == thread_id,
            EntityChatMessage.sender_id != user_id,
            EntityChatMessage.read_at.is_(None),
        )
        .all()
    )
