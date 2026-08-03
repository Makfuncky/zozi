"""Chat Enrichment — typing indicators, emoji reactions, legal hold, voice notes, message edit/delete."""
from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import text, table, column, select, update, delete

from models.employee_models import Employee
from utils.datetime_utils import utcnow as _utcnow
from utils.websocket_manager import ws_manager

logger = logging.getLogger(__name__)

_ALLOWED_TABLES = frozenset({
    "direct_chat_messages",
    "group_chat_messages",
    "internal_messages",
})


def _validate_table_name(table_name: str) -> None:
    if table_name not in _ALLOWED_TABLES:
        raise ValueError(f"Invalid table name: {table_name}")


# ══════════════════════════════════════════════════════════════════
#  Typing Indicators (WebSocket)
# ══════════════════════════════════════════════════════════════════


async def send_typing_indicator(
    room_id: int,
    employee_id: int,
    room_type: str = "direct",
    is_typing: bool = True,
) -> None:
    """Broadcast typing indicator to all room participants via WebSocket."""
    event = "typing" if is_typing else "typing_stopped"
    try:
        await ws_manager.broadcast_to_room(
            room=f"{room_type}:{room_id}",
            message={
                "event": event,
                "employee_id": employee_id,
                "room_id": room_id,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )
    except Exception as e:
        logger.debug("Typing indicator broadcast failed: %s", e)


# ══════════════════════════════════════════════════════════════════
#  Emoji Reactions
# ══════════════════════════════════════════════════════════════════


def add_reaction(
    db: Session,
    message_id: int,
    message_type: str,
    employee_id: int,
    emoji: str,
) -> Dict[str, Any]:
    """Add an emoji reaction to a message (upsert)."""
    db.execute(
        text("""
            INSERT INTO chat_reactions (message_id, message_type, employee_id, emoji, created_at)
            VALUES (:msg_id, :msg_type, :emp_id, :emoji, :now)
            ON CONFLICT (message_id, message_type, employee_id, emoji)
            DO UPDATE SET created_at = EXCLUDED.created_at
        """).bindparams(
            msg_id=message_id,
            msg_type=message_type,
            emp_id=employee_id,
            emoji=emoji,
            now=_utcnow(),
        ),
    )
    db.commit()
    _log_activity(db, employee_id, "chat_reaction_added", f"chat_{message_type}", str(message_id))
    return {"message_id": message_id, "emoji": emoji, "employee_id": employee_id, "action": "added"}


def remove_reaction(
    db: Session,
    message_id: int,
    message_type: str,
    employee_id: int,
    emoji: str,
) -> Dict[str, Any]:
    """Remove an emoji reaction."""
    db.execute(
        text("""
            DELETE FROM chat_reactions
            WHERE message_id = :msg_id
              AND message_type = :msg_type
              AND employee_id = :emp_id
              AND emoji = :emoji
        """).bindparams(
            msg_id=message_id,
            msg_type=message_type,
            emp_id=employee_id,
            emoji=emoji,
        ),
    )
    db.commit()
    _log_activity(db, employee_id, "chat_reaction_removed", f"chat_{message_type}", str(message_id))
    return {"message_id": message_id, "emoji": emoji, "action": "removed"}


def get_reactions(
    db: Session,
    message_id: int,
    message_type: str,
) -> Dict[str, List[Dict[str, Any]]]:
    """Get all reactions for a message, grouped by emoji."""
    rows = db.execute(
        text("""
            SELECT emoji, employee_id, created_at
            FROM chat_reactions
            WHERE message_id = :msg_id AND message_type = :msg_type
            ORDER BY created_at ASC
        """).bindparams(
            msg_id=message_id,
            msg_type=message_type,
        ),
    ).mappings().all()

    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for r in rows:
        emoji = r["emoji"]
        if emoji not in grouped:
            grouped[emoji] = []
        grouped[emoji].append({
            "employee_id": r["employee_id"],
            "timestamp": r["created_at"].isoformat() if r["created_at"] else None,
        })
    return {"reactions": grouped, "total": sum(len(v) for v in grouped.values())}


# ══════════════════════════════════════════════════════════════════
#  Message Edit / Delete (with audit)
# ══════════════════════════════════════════════════════════════════


def edit_message(
    db: Session,
    message_id: int,
    message_type: str,
    new_body: str,
    employee_id: int,
) -> Dict[str, Any]:
    """Edit a message (only within edit window). Store original in audit."""
    tables = {
        "direct": table("direct_chat_messages",
            column("id"), column("sender_id"), column("body"),
        ),
        "group": table("group_chat_messages",
            column("id"), column("sender_id"), column("body"),
        ),
        "channel": table("internal_messages",
            column("id"), column("sender_id"), column("body"),
        ),
    }
    tbl = tables.get(message_type)
    if not tbl:
        raise ValueError(f"Unknown message type: {message_type}")

    _validate_table_name(tbl.name)

    # Get original
    original = db.execute(
        select(tbl.c.id, tbl.c.sender_id, tbl.c.body).where(tbl.c.id == message_id),
    ).mappings().first()
    if not original:
        raise ValueError("Message not found")
    if original["sender_id"] != employee_id:
        raise ValueError("Can only edit your own messages")

    # Audit log the original
    db.execute(
        text("""
            INSERT INTO communication_audit_trail
                (entity_type, entity_id, user_id, action, content_preview, metadata_json, created_at)
            VALUES
                (:entity_type, :entity_id, :user_id, 'message_edited',
                 :preview, :metadata, :now)
        """).bindparams(
            entity_type=f"{message_type}_message",
            entity_id=message_id,
            user_id=employee_id,
            preview=original["body"][:200],
            metadata=json.dumps({"original_body": original["body"], "new_body": new_body}),
            now=_utcnow(),
        ),
    )

    # Update
    db.execute(
        update(tbl).where(tbl.c.id == message_id).values(body=new_body),
    )
    db.commit()
    _log_activity(db, employee_id, "chat_message_edited", f"chat_{message_type}", str(message_id))
    return {"id": message_id, "body": new_body, "edited": True}


def delete_message(
    db: Session,
    message_id: int,
    message_type: str,
    employee_id: int,
    hard_delete: bool = False,
) -> Dict[str, Any]:
    """Soft-delete (default) or hard-delete a message. Audit logged."""
    tables = {
        "direct": table("direct_chat_messages",
            column("id"), column("sender_id"), column("body"),
        ),
        "group": table("group_chat_messages",
            column("id"), column("sender_id"), column("body"),
        ),
        "channel": table("internal_messages",
            column("id"), column("sender_id"), column("body"),
        ),
    }
    tbl = tables.get(message_type)
    if not tbl:
        raise ValueError(f"Unknown message type: {message_type}")

    _validate_table_name(tbl.name)

    original = db.execute(
        select(tbl.c.id, tbl.c.sender_id, tbl.c.body).where(tbl.c.id == message_id),
    ).mappings().first()
    if not original:
        raise ValueError("Message not found")

    # Audit
    db.execute(
        text("""
            INSERT INTO communication_audit_trail
                (entity_type, entity_id, user_id, action, content_preview, metadata_json, created_at)
            VALUES
                (:entity_type, :entity_id, :user_id, 'message_deleted',
                 :preview, :metadata, :now)
        """).bindparams(
            entity_type=f"{message_type}_message",
            entity_id=message_id,
            user_id=employee_id,
            preview=original["body"][:200],
            metadata=json.dumps({"deleted_by": employee_id, "hard_delete": hard_delete}),
            now=_utcnow(),
        ),
    )

    if hard_delete:
        db.execute(delete(tbl).where(tbl.c.id == message_id))
    else:
        db.execute(
            update(tbl).where(tbl.c.id == message_id).values(
                body="[deleted]", is_deleted=True,
            ),
        )
    db.commit()
    _log_activity(db, employee_id, "chat_message_deleted", f"chat_{message_type}", str(message_id))
    return {"id": message_id, "deleted": True, "hard_delete": hard_delete}


# ══════════════════════════════════════════════════════════════════
#  Legal Hold
# ══════════════════════════════════════════════════════════════════


def apply_legal_hold(
    db: Session,
    room_id: int,
    room_type: str,
    placed_by: int,
    reason: str,
) -> Dict[str, Any]:
    """Apply a legal hold on a chat room (freezes deletion)."""
    db.execute(
        text("""
            INSERT INTO chat_legal_holds (room_id, room_type, placed_by, reason, placed_at)
            VALUES (:room_id, :room_type, :placed_by, :reason, :now)
            ON CONFLICT (room_id, room_type) WHERE is_active = true
            DO NOTHING
        """).bindparams(
            room_id=room_id,
            room_type=room_type,
            placed_by=placed_by,
            reason=reason,
            now=_utcnow(),
        ),
    )
    db.commit()
    _log_activity(db, placed_by, "legal_hold_applied", f"chat_{room_type}_room", str(room_id))
    return {"room_id": room_id, "room_type": room_type, "legal_hold": True, "reason": reason}


def release_legal_hold(
    db: Session,
    room_id: int,
    room_type: str,
) -> Dict[str, Any]:
    """Release a legal hold on a chat room."""
    db.execute(
        text("""
            UPDATE chat_legal_holds
            SET is_active = false, released_at = :now
            WHERE room_id = :room_id AND room_type = :room_type AND is_active = true
        """).bindparams(
            room_id=room_id,
            room_type=room_type,
            now=_utcnow(),
        ),
    )
    db.commit()
    return {"room_id": room_id, "room_type": room_type, "legal_hold": False}


def is_legal_hold_active(db: Session, room_id: int, room_type: str) -> bool:
    """Check if a room has an active legal hold."""
    result = db.execute(
        text("""
            SELECT 1 FROM chat_legal_holds
            WHERE room_id = :room_id AND room_type = :room_type AND is_active = true
        """).bindparams(
            room_id=room_id,
            room_type=room_type,
        ),
    ).scalar()
    return bool(result)


# ══════════════════════════════════════════════════════════════════
#  Voice Note Helpers
# ══════════════════════════════════════════════════════════════════


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


def _log_activity(
    db: Session,
    actor_employee_id: int,
    action: str,
    entity_type: str,
    entity_id: str,
    target_employee_id: Optional[int] = None,
) -> None:
    try:
        from services.employee_activity_logger import log_activity
        log_activity(
            db=db,
            actor_employee_id=actor_employee_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            target_employee_id=target_employee_id,
        )
    except Exception as exc:
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Activity log failed (non-critical): %s", exc)
