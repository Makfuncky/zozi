"""Comms Service â€” encapsulates communication business logic."""

import base64
import logging
from datetime import datetime
from typing import List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from domains.comms.models.communication import ProxyChannel, TicketMessage
from domains.comms.models.communication_schema_models import SupportTicket
from domains.comms.models.marketing import (
    EmailCampaign,
    EmailRuntimeConfig,
    EmailSuppression,
    EmailTemplate,
)
class NotificationChannel:
    IN_APP = 'in_app'
    EMAIL = 'email'
    SMS = 'sms'
    PUSH = 'push'

class NotificationPriority:
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    URGENT = 'urgent'
from domains.governance.models.user import User
from domains.accounts.ports import get_user_by_id

logger = logging.getLogger(__name__)


def parse_channel(value: str) -> NotificationChannel:
    try:
        return NotificationChannel(value)
    except ValueError:
        return NotificationChannel.IN_APP


def parse_priority(value: str) -> NotificationPriority:
    try:
        return NotificationPriority(value)
    except ValueError:
        return NotificationPriority.MEDIUM


def get_ticket_payload(ticket: SupportTicket, replies: list = None) -> dict:
    msgs = replies if replies is not None else list(getattr(ticket, "messages", []) or [])
    first_message = msgs[0].message if msgs else ""
    return {
        "id": ticket.id,
        "user_id": ticket.user_id,
        "subject": ticket.subject,
        "message": first_message,
        "priority": ticket.priority,
        "status": ticket.status,
        "created_at": ticket.created_at,
        "updated_at": ticket.updated_at,
        "replies": [
            {
                "id": r.id,
                "ticket_id": r.ticket_id,
                "sender_id": r.sender_id,
                "message": r.message,
                "is_admin": bool(getattr(r, "is_admin", False)),
                "created_at": r.created_at,
            }
            for r in msgs
        ],
    }


def validate_ticket_input(payload: dict) -> tuple:
    subject = str(payload.get("subject") or "").strip()
    message = str(payload.get("message") or payload.get("body") or "").strip()
    priority = str(payload.get("priority") or "normal").strip().lower()
    if not subject:
        raise ValueError("subject is required")
    if len(message) < 10:
        raise ValueError("message must be at least 10 characters")
    if priority not in {"low", "normal", "high"}:
        raise ValueError("priority must be one of: low, normal, high")
    return subject, message, priority


def serialize_template(t) -> dict:
    return {
        "id": t.id,
        "name": t.name,
        "subject": t.subject,
        "content": t.content,
        "template_type": t.template_type,
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "updated_at": t.updated_at.isoformat() if t.updated_at else None,
    }


def email_runtime_to_dict(cfg) -> dict:
    resend_key = bool(cfg.resend_api_key)
    resend_secret = bool(cfg.resend_webhook_secret)
    return {
        "id": cfg.id,
        "provider": cfg.provider,
        "active_provider": cfg.provider,
        "source": "db",
        "available": True,
        "live": cfg.provider not in ("disabled", None),
        "preview_only": cfg.provider == "environment",
        "supports_webhooks": True,
        "smtp_host": cfg.smtp_host,
        "smtp_port": cfg.smtp_port or 587,
        "smtp_username": cfg.smtp_username,
        "smtp_use_tls": cfg.smtp_use_tls,
        "smtp_use_ssl": cfg.smtp_use_ssl,
        "smtp_timeout_seconds": cfg.smtp_timeout_seconds or 15,
        "email_from_default": cfg.email_from_default,
        "email_from_promotional": cfg.email_from_promotional,
        "email_from_transactional": cfg.email_from_transactional,
        "email_from_notification": cfg.email_from_notification,
        "email_from_alert": cfg.email_from_alert,
        "email_from_verification": cfg.email_from_verification,
        "email_from_login_verification": cfg.email_from_login_verification,
        "email_from_password_reset": cfg.email_from_password_reset,
        "resend_api_key_configured": resend_key,
        "resend_webhook_secret_configured": resend_secret,
        "smtp_password_configured": bool(cfg.smtp_password),
    }


def get_unified_inbox(db: Session, current_user: dict, lens: str = "all", cursor: str = None, limit: int = 50, transport: str = None) -> dict:
    """Return a cursor-paginated, server-sorted merge of all conversation types."""
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

    sql = """
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

    user_id = int(current_user.get("id", 0))
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


def list_email_templates(db: Session, page: int = 1, limit: int = 50) -> dict:
    """Return paginated email templates."""
    from infrastructure.utils.pagination import paginated_response
    query = db.query(EmailTemplate).order_by(EmailTemplate.created_at.desc())
    return paginated_response(query, page=page, size=limit, max_size=100)


def list_email_campaigns(db: Session, page: int = 1, limit: int = 50) -> dict:
    """Return paginated email campaigns."""
    from infrastructure.utils.pagination import paginated_response
    query = db.query(EmailCampaign).order_by(EmailCampaign.created_at.desc())
    return paginated_response(query, page=page, size=limit, max_size=100)


def list_email_suppressions(db: Session, status: Optional[str] = None) -> list:
    """Return email suppressions, optionally filtered by status."""
    q = db.query(EmailSuppression)
    if status:
        q = q.filter(EmailSuppression.status_code == status)
    suppressions = q.all()
    return [
        {
            "id": s.id,
            "email": s.email,
            "reason": s.reason,
            "source": s.source,
            "provider": s.provider,
            "status": s.status_code,
            "notes": s.notes,
            "suppressed_at": s.suppressed_at.isoformat() if s.suppressed_at else None,
            "last_event_at": s.last_event_at.isoformat() if s.last_event_at else None,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in suppressions
    ]


def update_email_suppression(db: Session, suppression_id: int, body: dict) -> dict:
    """Update an email suppression record."""
    from infrastructure.utils.datetime_utils import utcnow as _utcnow
    s = db.query(EmailSuppression).filter(EmailSuppression.id == suppression_id).first()
    if not s:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Suppression not found")
    if "status" in body:
        s.status_code = body["status"]
        if body["status"] == "active" and not s.suppressed_at:
            s.suppressed_at = _utcnow()
        s.last_event_at = _utcnow()
    if "reason" in body:
        s.reason = body["reason"]
    if "notes" in body:
        s.notes = body["notes"]
    db.commit()
    db.refresh(s)
    return {
        "id": s.id,
        "email": s.email,
        "reason": s.reason,
        "source": s.source,
        "provider": s.provider,
        "status": s.status_code,
        "notes": s.notes,
        "suppressed_at": s.suppressed_at.isoformat() if s.suppressed_at else None,
        "last_event_at": s.last_event_at.isoformat() if s.last_event_at else None,
    }


def create_email_campaign(db: Session, payload: dict, current_user: dict) -> dict:
    """Create a new email campaign."""
    campaign = EmailCampaign(
        name=payload.get("name", "Untitled Campaign"),
        subject=payload.get("subject", ""),
        status_code=payload.get("status", "draft"),
        target_audience=payload.get("target_audience"),
        country_code=payload.get("country_code"),
        created_by=current_user.get("id") if isinstance(current_user, dict) else None,
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return {
        "id": campaign.id,
        "name": campaign.name,
        "subject": campaign.subject,
        "status": campaign.status_code,
        "created_at": campaign.created_at.isoformat() if campaign.created_at else None,
    }


def create_email_template(db: Session, payload: dict, current_user: dict) -> dict:
    """Create a new email template."""
    template = EmailTemplate(
        name=payload.get("name", ""),
        subject=payload.get("subject", ""),
        content=payload.get("content"),
        template_type=payload.get("template_type", "marketing"),
        created_by=current_user.get("id") if isinstance(current_user, dict) else None,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return serialize_template(template)


def update_email_template(db: Session, template_id: int, payload: dict) -> dict:
    """Update an existing email template."""
    template = db.query(EmailTemplate).filter(EmailTemplate.id == template_id).first()
    if not template:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Template not found")
    for field in ["name", "subject", "content", "template_type"]:
        if field in payload:
            setattr(template, field, payload[field])
    db.commit()
    db.refresh(template)
    return serialize_template(template)


def delete_email_template(db: Session, template_id: int) -> dict:
    """Delete an email template."""
    template = db.query(EmailTemplate).filter(EmailTemplate.id == template_id).first()
    if not template:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Template not found")
    db.delete(template)
    db.commit()
    return {"message": "Template deleted", "id": template_id}


def get_email_runtime_config(db: Session) -> dict:
    """Get or create the email runtime config."""
    cfg = db.query(EmailRuntimeConfig).order_by(EmailRuntimeConfig.id.asc()).first()
    if not cfg:
        cfg = EmailRuntimeConfig(provider="environment", smtp_port=587)
        db.add(cfg)
        db.commit()
        db.refresh(cfg)
    return email_runtime_to_dict(cfg)


def upsert_email_runtime_config(db: Session, payload: dict) -> dict:
    """Update or create the email runtime config."""
    cfg = db.query(EmailRuntimeConfig).order_by(EmailRuntimeConfig.id.asc()).first()
    if not cfg:
        cfg = EmailRuntimeConfig()
        db.add(cfg)
    simple_fields = [
        "provider", "smtp_host", "smtp_port", "smtp_username", "is_smtp_use_tls", "is_smtp_use_ssl",
        "smtp_timeout_seconds", "email_from_default", "email_from_promotional", "email_from_transactional",
        "email_from_notification", "email_from_alert", "email_from_verification", "email_from_login_verification",
        "email_from_password_reset",
    ]
    for field in simple_fields:
        if field in payload:
            setattr(cfg, field, payload[field])
    if payload.get("resend_api_key"):
        cfg.resend_api_key = payload["resend_api_key"]
    if payload.get("resend_webhook_secret"):
        cfg.resend_webhook_secret = payload["resend_webhook_secret"]
    if payload.get("smtp_password"):
        cfg.smtp_password = payload["smtp_password"]
    db.commit()
    db.refresh(cfg)
    return email_runtime_to_dict(cfg)


def get_proxy_channel_by_id(db: Session, channel_id: int) -> Optional[ProxyChannel]:
    """Look up a proxy channel by ID."""
    return db.query(ProxyChannel).filter_by(id=channel_id).first()


def list_user_proxy_channels(db: Session, user_id: int, page: int = 1, limit: int = 50) -> dict:
    """List proxy channels for a specific user."""
    from infrastructure.utils.pagination import paginated_response
    query = db.query(ProxyChannel).filter(ProxyChannel.participants.contains({"user_ids": [user_id]})).order_by(ProxyChannel.id)
    result = paginated_response(query, page=page, size=limit, max_size=100)
    from domains.comms.services.proxy_communication import get_proxy_service
    proxy_service = get_proxy_service(db)
    result["items"] = [
        {
            "id": c.id,
            "proxy_phone": proxy_service.mask_phone_number(c.proxy_phone) if c.proxy_phone else None,
            "proxy_email": c.proxy_email,
            "is_active": c.is_active,
        }
        for c in result["items"]
    ]
    return result


def list_all_proxy_channels(db: Session, page: int = 1, limit: int = 50) -> dict:
    """List all proxy channels (admin)."""
    from infrastructure.utils.pagination import paginated_response
    query = db.query(ProxyChannel).order_by(ProxyChannel.id)
    return paginated_response(query, page=page, size=limit, max_size=100)


def list_support_tickets(db: Session, current_user: dict, page: int = 1, page_size: int = 20) -> dict:
    """List support tickets visible to the current user."""
    q = db.query(SupportTicket)
    if current_user.role == "customer":
        q = q.filter(SupportTicket.user_id == current_user.id)
    total = q.count()
    tickets = q.order_by(SupportTicket.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {"data": [get_ticket_payload(t) for t in tickets], "total": total, "page": page, "page_size": page_size}


def create_support_ticket(db: Session, payload: dict, current_user: dict) -> dict:
    """Create a new support ticket with initial message."""
    subject, message, priority = validate_ticket_input(payload)
    ticket = SupportTicket(user_id=current_user.id, subject=subject, priority=priority)
    db.add(ticket)
    db.flush()
    initial = TicketMessage(ticket_id=ticket.id, sender_id=current_user.id, message=message)
    db.add(initial)
    db.commit()
    db.refresh(ticket)
    return get_ticket_payload(ticket)


def get_support_ticket(db: Session, ticket_id: int, current_user: dict) -> dict:
    """Get a single support ticket with replies."""
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        from fastapi import HTTPException
        raise HTTPException(404)
    if current_user.role == "customer" and ticket.user_id != current_user.id:
        from fastapi import HTTPException
        raise HTTPException(404)
    replies = db.query(TicketMessage).filter(TicketMessage.ticket_id == ticket_id).order_by(TicketMessage.created_at.asc()).all()
    return get_ticket_payload(ticket, replies)


def reply_to_support_ticket(db: Session, ticket_id: int, payload: dict, current_user: dict) -> dict:
    """Add a reply message to a support ticket."""
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        from fastapi import HTTPException
        raise HTTPException(404)
    if current_user.role == "customer" and ticket.user_id != current_user.id:
        from fastapi import HTTPException
        raise HTTPException(404)
    message = str(payload.get("message") or payload.get("body") or "").strip()
    if len(message) < 1:
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail="message is required")
    msg = TicketMessage(ticket_id=ticket_id, sender_id=current_user.id, message=message)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return {
        "id": msg.id,
        "ticket_id": msg.ticket_id,
        "sender_id": msg.sender_id,
        "message": msg.message,
        "created_at": msg.created_at,
    }


def get_employee_inbox(db: Session, employee_id: int, folder: str = "inbox", limit: int = 50, offset: int = 0) -> dict:
    """Return employee inbox messages."""
    return {"employee_id": employee_id, "folder": folder, "limit": limit, "offset": offset, "messages": []}

