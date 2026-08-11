"""Chat write controller.

Thin orchestration between the WebSocket router and
``services.comms.chat_write_service``. Satisfies CIR2 (routers → controllers →
services); all DB writes live in the service. Exposed under the same names the
router already calls (``_persist_message`` / ``_mark_messages_read``) so the
call sites are unchanged.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from services.comms.chat_write_service import (
    mark_messages_read as _mark_messages_read,
    persist_message as _persist_message,
)
from services.core.user_read_service import (
    get_user_display_name as _get_user_display_name,
    get_user_role as _get_user_role,
)
import structlog
logger = structlog.get_logger(__name__)


def persist_message(db, room_id: str, sender_id: int, content: str, msg_type: str = "text"):
    return _persist_message(db, room_id, sender_id, content, msg_type)


def mark_messages_read(db, room_id: str, user_id: int) -> int:
    return _mark_messages_read(db, room_id, user_id)


def get_user_display_name(db: Session, user_id: int) -> str:
    return _get_user_display_name(db, user_id)


def get_user_role(db: Session, user_id: int) -> str:
    return _get_user_role(db, user_id)
