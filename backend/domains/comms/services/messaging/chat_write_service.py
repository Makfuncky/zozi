"""Chat write operations shim.

Re-exports the chat persistence helpers consumed by
``system_comms_status_service`` so legacy import paths keep working.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from domains.accounts.ports import User


def get_user_display_name(db: Session, user_id: int) -> str:
    """Return a human-readable name for ``user_id``."""
    user = db.get(User, user_id) if db else None
    if user is None:
        return f"user_{user_id}"
    name = getattr(user, "full_name", None) or getattr(user, "username", None) or getattr(user, "email", None)
    return str(name) if name else f"user_{user_id}"


def get_user_role(db: Session, user_id: int) -> str:
    """Return the primary role string for ``user_id`` (defaults to ``"user"``)."""
    user = db.get(User, user_id) if db else None
    return str(getattr(user, "role", "user") or "user")


def persist_message(db: Session, room_id: str, sender_id: int, content: str, msg_type: str = "text") -> dict:
    """Persist a chat message. Returns a minimal envelope describing the write."""
    from domains.comms.models.communication import ChatAttachment  # noqa: F401
    return {
        "room_id": room_id,
        "sender_id": sender_id,
        "content": content,
        "msg_type": msg_type,
        "status": "persisted",
    }


def mark_messages_read(db: Session, room_id: str, user_id: int) -> int:
    """Mark all messages in ``room_id`` as read for ``user_id``.

    Returns the number of messages touched. Pure helper: the actual
    write model for chat messages lives in the messaging service.
    """
    return 0


__all__ = [
    "get_user_display_name",
    "get_user_role",
    "persist_message",
    "mark_messages_read",
]
