"""Unified inbox service.

Encapsulates all DB access for the unified inbox endpoints so the router
stays a thin orchestration layer (W1: routers/controllers must not write to
the DB). Previously this logic lived inline in ``routers/comms_unified.py``.
"""
from __future__ import annotations

import base64
import logging

from sqlalchemy import text
from sqlalchemy.orm import Session

from utils.audit import audit_log
import structlog
logger = structlog.get_logger(__name__)

logger = logging.getLogger(__name__)


def _log_reset(
    db: Session,
    *,
    user_id,
    username,
    user_role,
    ip_address: str,
    status: str,
    error: str | None = None,
) -> None:
    # NOTE: uses the real audit_log(...) signature from utils.audit. The
    # original router call used non-existent kwargs (user_id, resource_type,
    # status) and a missing AuditAction.INBOX_RESET, so the endpoint never
    # worked at runtime — this fixes it as part of the W1 move into a service.
    audit_log(
        db,
        actor_id=user_id,
        action="inbox_reset",
        entity="comms",
        entity_key="unified_inbox",
        details={
            "username": username,
            "role": user_role,
            "status": status,
            "action": "reset_unified_inbox",
            "endpoint": "/comms/unified-inbox/reset",
            **({"error": error} if error else {}),
        },
        ip_address=ip_address,
    )


def reset_unified_inbox(
    db: Session,
    *,
    user_id,
    username,
    user_role,
    ip_address: str,
) -> dict:
    """Clear and re-seed unified-inbox demo data, auditing the result.

    ``seed_comms`` manages its own session internally. The audit entry is
    written on the supplied ``db`` session. Raises on failure (after writing a
    failure audit entry) so the router can convert it into an HTTP 500.
    """
    from jobs.seed_all import seed_comms

    try:
        seed_comms()
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as exc:
        _log_reset(
            db,
            user_id=user_id,
            username=username,
            user_role=user_role,
            ip_address=ip_address,
            status="failure",
            error=str(exc),
        )
        raise

    _log_reset(
        db,
        user_id=user_id,
        username=username,
        user_role=user_role,
        ip_address=ip_address,
        status="success",
    )
    return {"status": "ok", "message": "Communication data reset and re-seeded successfully"}


def get_unified_inbox(
    db: Session,
    *,
    user_id: int,
    lens: str = "all",
    cursor: str | None = None,
    limit: int = 50,
    transport: str | None = None,
) -> dict:
    """Cursor-paginated, server-sorted merge of all conversation types.

    Mirrors the prior inline SQL exactly; the only behavioural change is that
    the query now executes inside the service rather than the router.
    """
    where = "1=1"
    params: dict = {"limit": limit + 1, "user_id": user_id}  # fetch +1 for has_more

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
        except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as e:
            logger.exception("get_unified_inbox_failed", error=str(e))

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