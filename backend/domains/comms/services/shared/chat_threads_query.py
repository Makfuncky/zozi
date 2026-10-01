"""Shared chat threads query for unified inbox.

This module contains the complex SQL query used by both comms_service.py
and email_management.py to fetch unified inbox data. Extracting it here
eliminates duplication and ensures consistency.
"""
from __future__ import annotations

import base64
import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def build_unified_inbox_sql(where_clause: str) -> str:
    """Build the unified inbox SQL query.

    Args:
        where_clause: The WHERE clause to apply to the outer query.

    Returns:
        The complete SQL query string.
    """
    return """
        SELECT * FROM (
            SELECT
                'dm_' || dcr.id AS id,
                dcr.id AS local_id,
                'chat' AS transport,
                u.full_name AS title,
                SUBSTR(dcm.message, 1, 120) AS preview,
                CASE WHEN dcm.read_at IS NULL AND dcm.sender_id != :user_id THEN 1 ELSE 0 END AS unread,
                dcm.created_at AS updated_at,
                'direct' AS channel_type,
                0 AS participants,
                NULL AS peer_avatar,
                NULL AS folder
            FROM direct_chat_messages dcm
            JOIN direct_chat_rooms dcr ON dcr.id = dcm.room_id
            JOIN users u ON u.id = CASE WHEN dcr.participant_one = :user_id THEN dcr.participant_two ELSE dcr.participant_one END
            WHERE :user_id IN (dcr.participant_one, dcr.participant_two)

            UNION ALL

            SELECT
                'grp_' || gcm.id,
                gcm.id,
                'group',
                gcr.name,
                SUBSTR(gcm.message, 1, 120),
                CASE WHEN gcm.read_at IS NULL AND gcm.sender_id != :user_id THEN 1 ELSE 0 END,
                gcm.created_at,
                'group',
                (SELECT COUNT(*) FROM group_chat_members WHERE room_id = gcr.id),
                NULL,
                NULL AS folder
            FROM group_chat_messages gcm
            JOIN group_chat_rooms gcr ON gcr.id = gcm.room_id
            JOIN group_chat_members gcmem ON gcmem.room_id = gcr.id AND gcmem.user_id = :user_id

            UNION ALL

            SELECT
                'ch_' || im.id,
                im.id,
                'group',
                ic.name,
                SUBSTR(im.message, 1, 120),
                CASE WHEN im.read_at IS NULL AND im.user_id != :user_id THEN 1 ELSE 0 END,
                im.created_at,
                'channel',
                (SELECT COUNT(*) FROM internal_channel_members WHERE channel_id = ic.id),
                NULL,
                NULL AS folder
            FROM internal_messages im
            JOIN internal_channels ic ON ic.id = im.channel_id
            JOIN internal_channel_members icm ON icm.channel_id = ic.id AND icm.user_id = :user_id

            UNION ALL

            SELECT
                'eml_' || ie.id,
                ie.id,
                'email',
                ie.subject,
                SUBSTR(ie.body_text, 1, 120),
                CASE WHEN ef.name = 'inbox' THEN 1 ELSE 0 END,
                ie.created_at,
                'email',
                0,
                NULL,
                ef.name
            FROM internal_emails ie
            JOIN email_folders ef ON ef.id = ie.folder_id
            JOIN employees e ON e.id = ef.employee_id AND e.user_id = :user_id

        ) AS inbox
        WHERE """ + where_clause + """
        ORDER BY updated_at DESC, id DESC
        LIMIT :limit
    """


def execute_unified_inbox_query(
    db: Session,
    user_id: int,
    lens: str = "all",
    cursor: str | None = None,
    limit: int = 50,
    transport: str | None = None,
) -> dict:
    """Execute the unified inbox query and return formatted results.

    Args:
        db: Database session.
        user_id: The current user's ID.
        lens: Filter lens ("all", "unread", "mentions").
        cursor: Pagination cursor.
        limit: Maximum number of results.
        transport: Optional transport filter.

    Returns:
        Dict with items, nextCursor, and hasMore.
    """
    conditions = ["1=1"]
    params: dict = {"limit": limit + 1}

    if transport:
        conditions.append("transport = :transport")
        params["transport"] = transport

    if lens == "unread":
        conditions.append("unread > 0")
    elif lens == "mentions":
        conditions.append("channel_type = 'mention'")

    if cursor:
        try:
            decoded = base64.urlsafe_b64decode(cursor).decode()
            ts, cid = decoded.split("::", 1)
            conditions.append("(updated_at, id) < (:cursor_ts, :cursor_id)")
            params["cursor_ts"] = ts
            params["cursor_id"] = int(cid) if cid.isdigit() else cid
        except Exception:
            logger.warning("Invalid cursor supplied, falling back to first page", extra={"cursor": cursor})

    where_clause = " AND ".join(conditions)
    sql = build_unified_inbox_sql(where_clause)

    params["user_id"] = user_id

    rows = db.execute(text(sql), params).mappings().all()

    has_more = len(rows) > limit
    if has_more:
        rows = rows[:limit]

    items = []
    next_cursor = None
    for r in rows:
        ts = r["updated_at"]
        if hasattr(ts, "isoformat"):
            ts = ts.isoformat()
        items.append({
            "id": str(r["id"]),
            "transport": r["transport"],
            "title": r["title"],
            "preview": r["preview"],
            "unread": r["unread"],
            "updatedAt": ts,
            "channelType": r["channel_type"],
            "participants": r["participants"] or 0,
            "peerAvatar": r["peer_avatar"],
            "folder": r["folder"],
        })

    if has_more and rows:
        last = rows[-1]
        ts = last["updated_at"]
        if hasattr(ts, "isoformat"):
            ts = ts.isoformat()
        raw = f"{ts}::{last['local_id']}"
        next_cursor = base64.urlsafe_b64encode(raw.encode()).decode()

    return {"items": items, "nextCursor": next_cursor, "hasMore": has_more}
