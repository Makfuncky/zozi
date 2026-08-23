"""Auto-split from chat_enrichment.py: _message_ops."""
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
            now=utcnow(),
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
            now=utcnow(),
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

