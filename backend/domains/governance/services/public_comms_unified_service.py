"""Unified Inbox — cursor-paginated merge of all communication channels."""
from __future__ import annotations
import logging
from fastapi import Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from infrastructure.database.database import get_db
from domains.accounts.models.user import User
from infrastructure.utils.dependencies import get_current_user, require_admin
from infrastructure.utils.audit import AuditAction, audit_log
from infrastructure.utils.ip_utils import get_ip_for_logging
logger = logging.getLogger('zozi.api.comms')

def unified_inbox(lens: str=Query('all'), cursor: str | None=Query(None), limit: int=Query(50, ge=1, le=200), transport: str | None=Query(None), db: Session=Depends(get_db), current_user: dict=Depends(get_current_user)):
    """Return a cursor-paginated, server-sorted merge of all conversation
    types — DMs, group mentions, channel posts, internal emails — each as
    a normalized row.

    The unified inbox is powered by a UNION of all message sources ordered
    by `updated_at DESC`. `cursor` is a base64-encoded `<updated_at>::<id>`
    pair from the last visible row so the client requests the next page.
    """
    import base64, json
    where = '1=1'
    params: dict = {'limit': limit + 1}
    if transport:
        where += ' AND transport = :transport'
        params['transport'] = transport
    if lens == 'unread':
        where += ' AND unread > 0'
    elif lens == 'mentions':
        where += " AND channel_type = 'mention'"
    if cursor:
        try:
            decoded = base64.urlsafe_b64decode(cursor).decode()
            (ts, cid) = decoded.split('::', 1)
            where += ' AND (updated_at, id) < (:cursor_ts, :cursor_id)'
            params['cursor_ts'] = ts
            params['cursor_id'] = int(cid) if cid.isdigit() else cid
        except Exception:
            pass
    sql = f"\n        SELECT * FROM (\n            -- Direct messages\n            SELECT\n                'dm_' || dcr.id AS id,\n                dcr.id AS local_id,\n                'chat' AS transport,\n                u.full_name AS title,\n                SUBSTR(dcm.message, 1, 120) AS preview,\n                CASE WHEN dcm.read_at IS NULL AND dcm.sender_id != :user_id THEN 1 ELSE 0 END AS unread,\n                dcm.created_at AS updated_at,\n                'direct' AS channel_type,\n                0 AS participants,\n                NULL AS peer_avatar,\n                NULL AS folder\n            FROM direct_chat_messages dcm\n            JOIN direct_chat_rooms dcr ON dcr.id = dcm.room_id\n            JOIN users u ON u.id = CASE WHEN dcr.participant_one = :user_id THEN dcr.participant_two ELSE dcr.participant_one END\n            WHERE :user_id IN (dcr.participant_one, dcr.participant_two)\n\n            UNION ALL\n\n            -- Group messages\n            SELECT\n                'grp_' || gcm.id,\n                gcm.id,\n                'group',\n                gcr.name,\n                SUBSTR(gcm.message, 1, 120),\n                CASE WHEN gcm.read_at IS NULL AND gcm.sender_id != :user_id THEN 1 ELSE 0 END,\n                gcm.created_at,\n                'group',\n                (SELECT COUNT(*) FROM group_chat_members WHERE room_id = gcr.id),\n                NULL,\n                NULL AS folder\n            FROM group_chat_messages gcm\n            JOIN group_chat_rooms gcr ON gcr.id = gcm.room_id\n            JOIN group_chat_members gcmem ON gcmem.room_id = gcr.id AND gcmem.user_id = :user_id\n\n            UNION ALL\n\n            -- Internal channels\n            SELECT\n                'ch_' || im.id,\n                im.id,\n                'group',\n                ic.name,\n                SUBSTR(im.message, 1, 120),\n                CASE WHEN im.read_at IS NULL AND im.user_id != :user_id THEN 1 ELSE 0 END,\n                im.created_at,\n                'channel',\n                (SELECT COUNT(*) FROM internal_channel_members WHERE channel_id = ic.id),\n                NULL,\n                NULL AS folder\n            FROM internal_messages im\n            JOIN internal_channels ic ON ic.id = im.channel_id\n            JOIN internal_channel_members icm ON icm.channel_id = ic.id AND icm.user_id = :user_id\n\n            UNION ALL\n\n            -- Internal emails\n            SELECT\n                'eml_' || ie.id,\n                ie.id,\n                'email',\n                ie.subject,\n                SUBSTR(ie.body_text, 1, 120),\n                CASE WHEN ef.name = 'inbox' THEN 1 ELSE 0 END,\n                ie.created_at,\n                'email',\n                0,\n                NULL,\n                ef.name\n            FROM internal_emails ie\n            JOIN email_folders ef ON ef.id = ie.folder_id\n            JOIN employees e ON e.id = ef.employee_id AND e.user_id = :user_id\n\n        ) AS inbox\n        WHERE {where}\n        ORDER BY updated_at DESC, id DESC\n        LIMIT :limit\n    "
    user_id = int(current_user.id)
    params['user_id'] = user_id
    rows = db.execute(text(sql), params).mappings().all()
    has_more = len(rows) > limit
    if has_more:
        rows = rows[:limit]
    items = []
    next_cursor = None
    for r in rows:
        ts = r['updated_at']
        if hasattr(ts, 'isoformat'):
            ts = ts.isoformat()
        items.append({'id': str(r['id']), 'transport': r['transport'], 'title': r['title'], 'preview': r['preview'], 'unread': r['unread'], 'updatedAt': ts, 'channelType': r['channel_type'], 'participants': r['participants'] or 0, 'peerAvatar': r['peer_avatar'], 'folder': r['folder']})
    if has_more and rows:
        last = rows[-1]
        ts = last['updated_at']
        if hasattr(ts, 'isoformat'):
            ts = ts.isoformat()
        raw = f"{ts}::{last['local_id']}"
        next_cursor = base64.urlsafe_b64encode(raw.encode()).decode()
    return {'items': items, 'nextCursor': next_cursor, 'hasMore': has_more}
