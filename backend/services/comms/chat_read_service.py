"""Service methods for WebSocket chat data access."""
from __future__ import annotations
from sqlalchemy.orm import Session
from data.models import User
from data.models_core import DirectChatRoom, GroupChatRoom, EntityChatThread, EntityChatMessage, DirectChatMessage, GroupChatMessage
from data.models_communication import GroupChatMember
from utils.pagination import SAFE_QUERY_LIMIT
import structlog
logger = structlog.get_logger(__name__)


def get_direct_chat_room_by_id(db: Session, chat_id: str) -> DirectChatRoom | None:
    """Get a direct chat room by its chat_id."""
    return db.query(DirectChatRoom).filter(DirectChatRoom.chat_id == chat_id).first()


def get_group_chat_room_by_id(db: Session, chat_id: str) -> GroupChatRoom | None:
    """Get a group chat room by its chat_id."""
    return db.query(GroupChatRoom).filter(GroupChatRoom.chat_id == chat_id).first()


def get_entity_thread_by_id(db: Session, thread_id: int) -> EntityChatThread | None:
    """Get an entity chat thread by ID."""
    return db.query(EntityChatThread).filter(EntityChatThread.id == thread_id).first()


def check_room_access(db: Session, room_id: str, user_id: int, role: str = "") -> tuple[bool, bool]:
    """Check whether ``user_id`` may access the chat room ``room_id``.

    Returns ``(room_exists, user_is_member)`` so callers can distinguish a
    missing room (404/4004) from a forbidden membership (403/4003).

    - DM rooms: caller must be ``participant_one`` / ``participant_two``.
    - Group rooms: caller must have a ``GroupChatMember`` row.
    - Entity threads: no membership model exists (``get_entity_participants``
      always returns ``[]``), so access is restricted to staff roles.
    """
    if room_id.startswith("dm_"):
        room = get_direct_chat_room_by_id(db, room_id)
        if not room:
            return False, False
        return True, user_id in (room.participant_one, room.participant_two)
    if room_id.startswith("group_"):
        room = get_group_chat_room_by_id(db, room_id)
        if not room:
            return False, False
        member = (
            db.query(GroupChatMember)
            .filter(GroupChatMember.room_id == room.id, GroupChatMember.user_id == user_id)
            .first()
        )
        return True, member is not None
    # Entity thread (numeric room id)
    try:
        thread_id = int(room_id)
    except (TypeError, ValueError) as e:
        logger.exception("check_room_access_failed", error=str(e))
        return False, False
    thread = get_entity_thread_by_id(db, thread_id)
    if not thread:
        return False, False
    from utils.constants import STAFF_ROLES
    return True, role in STAFF_ROLES


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
        .limit(SAFE_QUERY_LIMIT).all()
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
        .limit(SAFE_QUERY_LIMIT).all()
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
        .limit(SAFE_QUERY_LIMIT).all()
    )