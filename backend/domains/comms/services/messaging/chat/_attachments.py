"""Auto-split from chat_enrichment.py: _attachments."""
from __future__ import annotations

"""Chat Enrichment — typing indicators, emoji reactions, legal hold, voice notes, message edit/delete."""
from infrastructure.utils.pagination import SAFE_QUERY_LIMIT

import json
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import text, table, column, select, update, delete

from domains.hr.ports import Employee
from infrastructure.utils.datetime_utils import utcnow as utcnow
from infrastructure.utils.websocket_manager import ws_manager
import structlog
logger = structlog.get_logger(__name__)

logger = logging.getLogger(__name__)

ALLOWED_TABLES = frozenset({
    "direct_chat_messages",
    "group_chat_messages",
    "internal_messages",
})


def create_voice_note_attachment(
    db: Session,
    message_id: int,
    message_type: str,
    file_url: str,
    file_name: str,
    file_size_bytes: int,
    duration_seconds: int,
    waveform_json: Optional[list] = None,
) -> Dict[str, Any]:
    """Create a voice note attachment record."""
    result = db.execute(
        text("""
            INSERT INTO chat_attachments
                (message_id, message_type, attachment_type, file_url, file_name,
                 file_size_bytes, mime_type, duration_seconds, waveform_json, is_processed)
            VALUES
                (:msg_id, :msg_type, 'voice', :file_url, :file_name,
                 :file_size, 'audio/ogg', :duration, :waveform, TRUE)
            RETURNING id
        """).bindparams(
            msg_id=message_id,
            msg_type=message_type,
            file_url=file_url,
            file_name=file_name,
            file_size=file_size_bytes,
            duration=duration_seconds,
            waveform=json.dumps(waveform_json) if waveform_json else None,
        ),
    )
    attachment_id = result.scalar()
    db.commit()
    return {"id": attachment_id, "type": "voice", "duration_seconds": duration_seconds}


def upload_attachment(
    db: Session,
    message_id: int,
    message_type: str,
    attachment_type: str,
    file_url: str,
    file_name: str,
    file_size_bytes: int,
    mime_type: str,
    duration_seconds: Optional[int] = None,
    thumbnail_url: Optional[str] = None,
    width: Optional[int] = None,
    height: Optional[int] = None,
) -> Dict[str, Any]:
    """Upload any attachment type (image, video, document)."""
    result = db.execute(
        text("""
            INSERT INTO chat_attachments
                (message_id, message_type, attachment_type, file_url, file_name,
                 file_size_bytes, mime_type, duration_seconds, thumbnail_url,
                 width, height, is_processed)
            VALUES
                (:msg_id, :msg_type, :att_type, :file_url, :file_name,
                 :file_size, :mime, :duration, :thumb,
                 :width, :height, FALSE)
            RETURNING id
        """).bindparams(
            msg_id=message_id,
            msg_type=message_type,
            att_type=attachment_type,
            file_url=file_url,
            file_name=file_name,
            file_size=file_size_bytes,
            mime=mime_type,
            duration=duration_seconds,
            thumb=thumbnail_url,
            width=width,
            height=height,
        ),
    )
    attachment_id = result.scalar()
    db.commit()
    return {"id": attachment_id, "type": attachment_type, "file_name": file_name}

