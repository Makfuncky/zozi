"""Chat Enrichment Router — emoji reactions, message edit/delete, legal hold, voice notes."""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from data.dependencies_auth import get_current_user
from data.db import get_db
from data.models import User
from services.chat_enrichment import (
    add_reaction,
    remove_reaction,
    get_reactions,
    edit_message,
    delete_message,
    apply_legal_hold,
    release_legal_hold,
    is_legal_hold_active,
    create_voice_note_attachment,
    upload_attachment,
    send_typing_indicator,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Reactions ────────────────────────────────────────────────────


@router.post("/reactions")
def api_add_reaction(
    message_id: int,
    message_type: str,
    emoji: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return add_reaction(db, message_id, message_type, current_user.id, emoji)


@router.delete("/reactions")
def api_remove_reaction(
    message_id: int,
    message_type: str,
    emoji: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return remove_reaction(db, message_id, message_type, current_user.id, emoji)


@router.get("/reactions/{message_type}/{message_id}")
def api_get_reactions(
    message_type: str,
    message_id: int,
    db: Session = Depends(get_db),
):
    return get_reactions(db, message_id, message_type)


# ── Message Edit / Delete ────────────────────────────────────────


@router.put("/messages/{message_type}/{message_id}")
def api_edit_message(
    message_type: str,
    message_id: int,
    body: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return edit_message(db, message_id, message_type, body, current_user.id)


@router.delete("/messages/{message_type}/{message_id}")
def api_delete_message(
    message_type: str,
    message_id: int,
    hard_delete: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return delete_message(db, message_id, message_type, current_user.id, hard_delete)


# ── Legal Hold ───────────────────────────────────────────────────


@router.post("/legal-hold")
def api_apply_legal_hold(
    room_id: int,
    room_type: str,
    reason: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return apply_legal_hold(db, room_id, room_type, current_user.id, reason)


@router.delete("/legal-hold/{room_type}/{room_id}")
def api_release_legal_hold(
    room_type: str,
    room_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return release_legal_hold(db, room_id, room_type)


@router.get("/legal-hold/{room_type}/{room_id}")
def api_check_legal_hold(
    room_type: str,
    room_id: int,
    db: Session = Depends(get_db),
):
    active = is_legal_hold_active(db, room_id, room_type)
    return {"room_id": room_id, "room_type": room_type, "legal_hold_active": active}


# ── Voice Note / Attachment Upload ───────────────────────────────


@router.post("/attachments/voice")
def api_upload_voice_note(
    message_id: int,
    message_type: str,
    file_url: str,
    file_name: str,
    file_size_bytes: int,
    duration_seconds: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_voice_note_attachment(
        db, message_id, message_type, file_url, file_name,
        file_size_bytes, duration_seconds,
    )


@router.post("/attachments")
def api_upload_attachment(
    message_id: int,
    message_type: str,
    attachment_type: str,
    file_url: str,
    file_name: str,
    file_size_bytes: int,
    mime_type: str,
    duration_seconds: Optional[int] = None,
    thumbnail_url: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return upload_attachment(
        db, message_id, message_type, attachment_type, file_url, file_name,
        file_size_bytes, mime_type, duration_seconds, thumbnail_url,
    )
