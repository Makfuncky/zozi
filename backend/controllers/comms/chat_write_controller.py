"""Chat write controller.

Thin orchestration between the WebSocket router and
``services.comms.chat_write_service``. Satisfies CIR2 (routers → controllers →
services); all DB writes live in the service. Exposed under the same names the
router already calls (``_persist_message`` / ``_mark_messages_read``) so the
call sites are unchanged.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from models import User
from services.comms.chat_write_service import (
    mark_messages_read as _mark_messages_read,
    persist_message as _persist_message,
)
import structlog
logger = structlog.get_logger(__name__)


def persist_message(db, room_id: str, sender_id: int, content: str, msg_type: str = "text"):
    return _persist_message(db, room_id, sender_id, content, msg_type)


def mark_messages_read(db, room_id: str, user_id: int) -> int:
    return _mark_messages_read(db, room_id, user_id)


def get_user_display_name(db: Session, user_id: int) -> str:
    """Return a human-readable display name for a user id."""
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        return f"User {user_id}"
    name = getattr(user, "full_name", None) or getattr(user, "display_name", None)
    if name:
        return name
    email = getattr(user, "email", None)
    return email or f"User {user_id}"


def get_user_role(db: Session, user_id: int) -> str:
    """Return the role string for a user id."""
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        return "unknown"
    return getattr(user, "role", "unknown") or "unknown"
