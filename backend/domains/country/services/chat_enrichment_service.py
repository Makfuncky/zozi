"""Auto-migrated service logic from routers/chat_enrichment.py."""
from __future__ import annotations

from __future__ import annotations

import logging

from typing import Optional

from fastapi import Depends

from sqlalchemy.orm import Session

from domains.governance.services.auth.auth_controller_service import get_current_user

from infrastructure.database.database import get_db

from domains.governance.models.user import User

from domains.comms.services.chat.chat_enrichment import add_reaction
from domains.comms.services.chat.chat_enrichment import apply_legal_hold
from domains.comms.services.chat.chat_enrichment import create_voice_note_attachment
from domains.comms.services.chat.chat_enrichment import delete_message
from domains.comms.services.chat.chat_enrichment import edit_message
from domains.comms.services.chat.chat_enrichment import get_reactions
from domains.comms.services.chat.chat_enrichment import is_legal_hold_active
from domains.comms.services.chat.chat_enrichment import release_legal_hold
from domains.comms.services.chat.chat_enrichment import remove_reaction
from domains.comms.services.chat.chat_enrichment import upload_attachment

logger = logging.getLogger(__name__)

def api_add_reaction(message_id: int, message_type: str, emoji: str, current_user: User, db: Session):
    return add_reaction(db, message_id, message_type, current_user.id, emoji)

def api_remove_reaction(message_id: int, message_type: str, emoji: str, current_user: User, db: Session):
    return remove_reaction(db, message_id, message_type, current_user.id, emoji)

def api_get_reactions(message_type: str, message_id: int, db: Session):
    return get_reactions(db, message_id, message_type)

def api_edit_message(message_type: str, message_id: int, body: str, current_user: User, db: Session):
    return edit_message(db, message_id, message_type, body, current_user.id)

def api_delete_message(message_type: str, message_id: int, hard_delete: bool, current_user: User, db: Session):
    return delete_message(db, message_id, message_type, current_user.id, hard_delete)

def api_apply_legal_hold(room_id: int, room_type: str, reason: str, current_user: User, db: Session):
    return apply_legal_hold(db, room_id, room_type, current_user.id, reason)

def api_release_legal_hold(room_type: str, room_id: int, current_user: User, db: Session):
    return release_legal_hold(db, room_id, room_type)

def api_check_legal_hold(room_type: str, room_id: int, db: Session):
    active = is_legal_hold_active(db, room_id, room_type)
    return {"room_id": room_id, "room_type": room_type, "legal_hold_active": active}

def api_upload_voice_note(message_id: int, message_type: str, file_url: str, file_name: str, file_size_bytes: int, duration_seconds: int, current_user: User, db: Session):
    return create_voice_note_attachment(
        db, message_id, message_type, file_url, file_name,
        file_size_bytes, duration_seconds,
    )

def api_upload_attachment(message_id: int, message_type: str, attachment_type: str, file_url: str, file_name: str, file_size_bytes: int, mime_type: str, duration_seconds: Optional[int], thumbnail_url: Optional[str], current_user: User, db: Session):
    return upload_attachment(
        db, message_id, message_type, attachment_type, file_url, file_name,
        file_size_bytes, mime_type, duration_seconds, thumbnail_url,
    )

