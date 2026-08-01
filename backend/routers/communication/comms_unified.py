"""Unified Inbox — cursor-paginated merge of all communication channels."""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session
from sqlalchemy import text

from db.database import get_db
from models import User
from utils.dependencies import get_current_user, require_admin
from utils.audit_log import AuditAction, audit_log
from utils.ip_utils import get_ip_for_logging

logger = logging.getLogger("zozi.api.comms")

router = APIRouter()


@router.get("/unified-inbox/reset")
def reset_unified_inbox(
    request: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Reset the unified inbox demo data.

    Admin-only endpoint that clears all communication seed data
    (entity threads, DMs, group chats, internal emails) and
    re-seeds it with realistic demo conversations.

    Useful for resetting the Communication workspace from the UI
    without requiring SSH or terminal access.

    Every reset is recorded in the audit log with the admin user's
    ID, timestamp, and IP address for traceability.
    """
    ip_address = get_ip_for_logging(request)

    try:
        from seed_comms import seed as _seed_comms
        _seed_comms()

        audit_log(
            db=db,
            action=AuditAction.INBOX_RESET,
            user_id=current_user.id,
            username=current_user.username or current_user.email,
            user_role=current_user.role,
            ip_address=ip_address,
            resource_type="comms",
            resource_id="unified_inbox",
            status="success",
            details={
                "action": "reset_unified_inbox",
                "endpoint": "/comms/unified-inbox/reset",
            },
        )

        return {
            "status": "ok",
            "message": "Communication data reset and re-seeded successfully",
        }
    except Exception as exc:
        logger.exception("Failed to reset unified inbox")

        audit_log(
            db=db,
            action=AuditAction.INBOX_RESET,
            user_id=current_user.id,
            username=current_user.username or current_user.email,
            user_role=current_user.role,
            ip_address=ip_address,
            resource_type="comms",
            resource_id="unified_inbox",
            status="failure",
            details={
                "action": "reset_unified_inbox",
                "endpoint": "/comms/unified-inbox/reset",
                "error": str(exc),
            },
        )

        raise HTTPException(
            status_code=500,
            detail=f"Failed to reset inbox: {str(exc)}",
        )


@router.get("/unified-inbox")
def unified_inbox(
    lens: str = Query("all"),
    cursor: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    transport: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Return a cursor-paginated, server-sorted merge of all conversation
    types — DMs, group mentions, channel posts, internal emails — each as
    a normalized row.

    The unified inbox is powered by a UNION of all message sources ordered
    by `updated_at DESC`. `cursor` is a base64-encoded `<updated_at>::<id>`
    pair from the last visible row so the client requests the next page.
    """
    import base64, json

    where = "1=1"
    params: dict = {"limit": limit + 1}  # fetch +1 for has_more

    if transport:
        where += " AND transport = :transport"
        params["transport"] = transport

    if lens == "unread":
        where += " AND unread > 0"
    elif lens == "mentions":
        where += " AND channel_type = 'mention'"

    if cursor:
        try:
            decoded = base64.urlsafe_b64decode(cursor).decode()
            ts, cid = decoded.split("::", 1)
            where += " AND (updated_at, id) < (:cursor_ts, :cursor_id)"
            params["cursor_ts"] = ts
            params["cursor_id"] = int(cid) if cid.isdigit() else cid
        except Exception:
            pass

    sql = f"""
        SELECT * FROM (
            -- Direct messages
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

            -- Group messages
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

            -- Internal channels
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

            -- Internal emails
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
        WHERE {where}
        ORDER BY updated_at DESC, id DESC
        LIMIT :limit
    """

    user_id = int(current_user.id)
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

