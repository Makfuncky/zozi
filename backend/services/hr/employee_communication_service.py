"""Employee Communication Service — internal chat, email, attachments, and threading.
Leverages existing models (direct_chat_rooms, direct_chat_messages, internal_channels,
employee_communication_threads) and gap-table additions (chat_attachments,
chat_read_receipts, internal_emails, email_folders).
"""

__all__ = [
    "send_chat_message",
    "get_chat_room",
    "get_chat_history",
    "mark_message_read",
    "create_channel",
    "send_channel_message",
    "get_channel_history",
    "send_internal_email",
    "get_inbox",
    "get_thread",
    "get_employee_directory",
]

import logging
from datetime import datetime, date
from typing import Optional, List, Dict, Any
import json

from sqlalchemy.orm import Session
from sqlalchemy import text, or_, and_

from data.models import User
from data.models_employee_models import Employee
from utils.datetime_utils import utcnow as _utcnow

logger = logging.getLogger(__name__)

# Maximum attachment size: 25MB
MAX_ATTACHMENT_SIZE = 25 * 1024 * 1024
ALLOWED_ATTACHMENT_TYPES = {
    "image/jpeg", "image/png", "image/webp", "image/gif",
    "video/mp4", "video/webm", "audio/mpeg", "audio/ogg", "audio/m4a",
    "application/pdf", "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}


# ════════════════════════════════════════════════════════════════
#  1:1 Chat
# ════════════════════════════════════════════════════════════════

def get_or_create_direct_room(db: Session, participant_a_id: int, participant_b_id: int) -> int:
    """Get an existing direct chat room between two employees, or create one."""
    import secrets

    p1, p2 = min(participant_a_id, participant_b_id), max(participant_a_id, participant_b_id)
    result = db.execute(
        text("""
            SELECT id FROM direct_chat_rooms
            WHERE (participant_one = :a AND participant_two = :b)
               OR (participant_one = :b AND participant_two = :a)
            LIMIT 1
        """),
        {"a": p1, "b": p2},
    ).scalar()

    if result:
        return result

    result = db.execute(
        text("""
            INSERT INTO direct_chat_rooms
                (chat_id, participant_one, participant_two, created_at)
            VALUES
                (:chat_id, :a, :b, :now)
            RETURNING id
        """),
        {"chat_id": f"dm_{secrets.token_hex(8)}", "a": p1, "b": p2, "now": _utcnow()},
    ).scalar()

    db.commit()
    return result


def send_chat_message(
    db: Session,
    sender_id: int,
    receiver_id: int,
    body: str,
    message_type: str = "text",
) -> Dict[str, Any]:
    """Send a 1:1 direct chat message."""
    room_id = get_or_create_direct_room(db, sender_id, receiver_id)

    result = db.execute(
        text("""
            INSERT INTO direct_chat_messages
                (room_id, sender_id, message, message_type, created_at)
            VALUES
                (:room_id, :sender_id, :body, :message_type, :now)
            RETURNING id, created_at
        """),
        {
            "room_id": room_id,
            "sender_id": sender_id,
            "body": body,
            "message_type": message_type,
            "now": _utcnow(),
        },
    )
    row = result.mappings().first()
    db.commit()

    _log_comm_event(db, sender_id, receiver_id, "chat_sent", "direct_chat_message", row["id"])

    created_at = row["created_at"]
    if isinstance(created_at, str):
        from datetime import datetime
        created_at = datetime.fromisoformat(created_at)

    return {
        "id": row["id"],
        "room_id": room_id,
        "sender_id": sender_id,
        "message": body,
        "body": body,
        "timestamp": created_at.isoformat() if created_at else None,
    }


def get_chat_room(db: Session, room_id: int, employee_id: int) -> Optional[Dict[str, Any]]:
    """Get a chat room with the other participant's details."""
    room = db.execute(
        text("""
            SELECT id, participant_one, participant_two, created_at
            FROM direct_chat_rooms WHERE id = :id
        """),
        {"id": room_id},
    ).mappings().first()
    if not room:
        return None

    if room["participant_one"] != employee_id and room["participant_two"] != employee_id:
        return None

    other_id = room["participant_two"] if room["participant_one"] == employee_id else room["participant_one"]
    other = db.query(Employee).filter(Employee.id == other_id).first()

    return {
        "id": room["id"],
        "other_employee": {
            "id": other.id if other else None,
            "employee_code": other.employee_code if other else None,
        },
        "created_at": room["created_at"].isoformat() if room["created_at"] else None,
    }


def get_chat_history(
    db: Session,
    room_id: int,
    limit: int = 50,
    before_id: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Get paginated chat history."""
    query = """
        SELECT id, room_id, sender_id, message, message_type, created_at
        FROM direct_chat_messages
        WHERE room_id = :room_id
    """
    params: Dict[str, Any] = {"room_id": room_id, "limit": limit}

    if before_id:
        query += " AND id < :before_id"
        params["before_id"] = before_id

    query += " ORDER BY created_at DESC LIMIT :limit"

    rows = db.execute(text(query), params).mappings().all()

    messages = []
    for r in reversed(rows):
        timestamp = r["created_at"]
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        msg = {
            "id": r["id"],
            "room_id": r["room_id"],
            "sender_id": r["sender_id"],
            "message": r["message"],
            "message_type": r["message_type"],
            "timestamp": timestamp.isoformat() if timestamp else None,
        }
        messages.append(msg)

    return messages


# ════════════════════════════════════════════════════════════════
#  Read Receipts
# ════════════════════════════════════════════════════════════════

def mark_message_read(db: Session, message_id: int, employee_id: int, message_type: str = "direct") -> Dict[str, Any]:
    """Mark a message as read by an employee."""
    db.execute(
        text("""
            INSERT INTO chat_read_receipts (message_id, message_type, employee_id, read_at)
            VALUES (:message_id, :message_type, :employee_id, :now)
            ON CONFLICT (message_id, message_type, employee_id) DO NOTHING
        """),
        {
            "message_id": message_id,
            "message_type": message_type,
            "employee_id": employee_id,
            "now": _utcnow(),
        },
    )
    db.commit()
    return {"message_id": message_id, "read_by": employee_id, "status": "read"}


# ════════════════════════════════════════════════════════════════
#  Channels (Slack-style)
# ════════════════════════════════════════════════════════════════

def create_channel(
    db: Session,
    name: str,
    created_by: Optional[int] = None,
    description: Optional[str] = None,
    is_public: bool = True,
    country_code: Optional[str] = None,
    allowed_roles: Optional[List[str]] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Create an internal channel aligned to the actual InternalChannel schema."""
    import secrets
    name = name.strip()
    if not name.startswith("#"):
        name = f"#{name}"

    existing = db.execute(
        text("SELECT id FROM internal_channels WHERE name = :name"),
        {"name": name},
    ).scalar()
    if existing:
        raise ValueError(f"Channel {name} already exists")

    channel_id = secrets.token_urlsafe(16)
    result = db.execute(
        text("""
            INSERT INTO internal_channels
                (channel_id, name, description, entity_type, entity_id, is_public,
                 is_active, created_by, country_code, allowed_roles, created_at)
            VALUES
                (:channel_id, :name, :description, :entity_type, :entity_id, :is_public,
                 :is_active, :created_by, :country_code, :allowed_roles, :now)
            RETURNING id
        """),
        {
            "channel_id": channel_id,
            "name": name,
            "description": description,
            "entity_type": entity_type or "global",
            "entity_id": entity_id or 0,
            "is_public": 1 if is_public else 0,
            "is_active": 1,
            "created_by": created_by,
            "country_code": country_code,
            "allowed_roles": json.dumps(allowed_roles or []),
            "now": _utcnow(),
        },
    )
    channel_db_id = result.scalar()
    db.commit()

    if created_by:
        try:
            db.execute(
                text("""
                    INSERT INTO internal_channel_members (channel_id, user_id, role, joined_at)
                    VALUES (:channel_id, :user_id, :role, :now)
                    ON CONFLICT DO NOTHING
                """),
                {"channel_id": channel_db_id, "user_id": created_by, "role": "admin", "now": _utcnow()},
            )
            db.commit()
        except Exception:
            db.rollback()

    return {"id": channel_db_id, "channel_id": channel_id, "name": name, "type": "channel"}


def send_channel_message(
    db: Session,
    channel_id: int,
    sender_id: int,
    message: str,
    message_type: str = "text",
) -> Dict[str, Any]:
    """Send a message to a channel."""
    result = db.execute(
        text("""
            INSERT INTO internal_messages
                (channel_id, user_id, message, message_type, created_at)
            VALUES
                (:channel_id, :sender_id, :message, :message_type, :now)
            RETURNING id, created_at
        """),
        {
            "channel_id": channel_id,
            "sender_id": sender_id,
            "message": message,
            "message_type": message_type,
            "now": _utcnow(),
        },
    )
    row = result.mappings().first()
    db.commit()

    _log_comm_event(db, sender_id, None, "channel_sent", "internal_message", row["id"])

    return {
        "id": row["id"],
        "channel_id": channel_id,
        "message": message,
        "timestamp": row["created_at"].isoformat() if row["created_at"] else None,
    }


def get_channel_history(
    db: Session,
    channel_id: int,
    limit: int = 50,
    before_id: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Get paginated channel message history."""
    query = """
        SELECT id, channel_id, user_id, message, message_type, created_at
        FROM internal_messages
        WHERE channel_id = :channel_id
    """
    params: Dict[str, Any] = {"channel_id": channel_id, "limit": limit}

    if before_id:
        query += " AND id < :before_id"
        params["before_id"] = before_id

    query += " ORDER BY created_at DESC LIMIT :limit"

    rows = db.execute(text(query), params).mappings().all()
    messages = []
    for r in reversed(rows):
        timestamp = r["created_at"]
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        msg = {
            "id": r["id"],
            "sender_id": r["user_id"],
            "message": r["message"],
            "message_type": r["message_type"],
            "timestamp": timestamp.isoformat() if timestamp else None,
        }
        messages.append(msg)

    return messages


# ════════════════════════════════════════════════════════════════
#  Internal Email
# ════════════════════════════════════════════════════════════════

def send_internal_email(
    db: Session,
    sender_id: int,
    recipient_ids: List[int],
    subject: str,
    body_html: str,
    cc_ids: Optional[List[int]] = None,
    attachment_ids: Optional[List[int]] = None,
    is_external: bool = False,
    external_to: Optional[str] = None,
) -> Dict[str, Any]:
    """Send an internal email. If recipients are internal employees,
    deliver in-database. If external, route to SMTP.
    """
    from data.models import User
    from models.communication import InternalEmail, EmailFolder
    from data.models_employee_models import Employee

    now = _utcnow()
    recipients_json = [{"user_id": uid} for uid in recipient_ids]
    cc_json = [{"user_id": cid} for cid in (cc_ids or [])]

    sender = db.query(User).filter(User.id == sender_id).first()
    country_code = None
    if sender:
        emp = db.query(Employee).filter(Employee.user_id == sender_id).first()
        if emp:
            country_code = emp.country_code

    email = InternalEmail(
        sender_id=sender_id,
        subject=subject,
        body_html=body_html,
        body_text=body_html,
        recipients=json.dumps(recipients_json + cc_json, default=str),
        thread_id=str(__import__("uuid").uuid4()),
        is_external=is_external,
        external_message_id=external_to,
        country_code=country_code,
        created_at=now,
        updated_at=now,
    )
    db.add(email)
    db.flush()

    if not email.thread_id:
        email.thread_id = str(email.id)
        db.flush()

    for uid in recipient_ids + (cc_ids or []):
        user = db.query(User).filter(User.id == uid).first()
        if not user:
            continue
        emp = getattr(user, "employee_profile", None)
        if emp and isinstance(emp, list):
            emp = emp[0] if emp else None
        if not emp:
            emp = db.query(Employee).filter(Employee.user_id == uid).first()
        if not emp:
            continue
        folder = (
            db.query(EmailFolder)
            .filter(EmailFolder.employee_id == emp.id, EmailFolder.name == "inbox")
            .first()
        )
        if not folder:
            folder = EmailFolder(employee_id=emp.id, name="inbox", folder_type="inbox", is_system=True)
            db.add(folder)
            db.flush()
        email.folder_id = folder.id

    db.commit()
    db.refresh(email)

    _log_comm_event(db, sender_id, recipient_ids[0] if recipient_ids else None, "email_sent", "internal_email", email.id)

    return {
        "id": email.id,
        "thread_id": email.thread_id,
        "subject": subject,
        "recipient_count": len(recipient_ids),
    }


def get_inbox(
    db: Session,
    employee_id: int,
    folder: str = "inbox",
    limit: int = 50,
    offset: int = 0,
) -> Dict[str, Any]:
    """Get emails in an employee's folder."""
    rows = db.execute(
        text("""
            SELECT e.id, e.sender_id, e.subject, e.body_html, e.thread_id,
                   e.recipients, e.created_at, ef.id as folder_id
            FROM internal_emails e
            JOIN email_folders ef ON e.folder_id = ef.id
            WHERE ef.employee_id = :eid AND ef.name = :folder
            ORDER BY e.created_at DESC
            LIMIT :limit OFFSET :offset
        """),
        {"eid": employee_id, "folder": folder, "limit": limit, "offset": offset},
    ).mappings().all()

    emails = []
    for r in rows:
        sender = db.execute(
            text("""
                SELECT u.full_name FROM users u
                JOIN employees e ON e.user_id = u.id
                WHERE e.id = :sid
            """),
            {"sid": r["sender_id"]},
        ).scalar()

        timestamp = r["created_at"]
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)

        emails.append({
            "id": r["id"],
            "sender_id": r["sender_id"],
            "sender_name": sender or f"#{r['sender_id']}",
            "subject": r["subject"],
            "body_preview": r["body_html"][:200] if r["body_html"] else "",
            "thread_id": r["thread_id"],
            "timestamp": timestamp.isoformat() if timestamp else None,
        })

    total = db.execute(
        text("""
            SELECT COUNT(*) FROM internal_emails e
            JOIN email_folders ef ON e.folder_id = ef.id
            WHERE ef.employee_id = :eid AND ef.name = :folder
        """),
        {"eid": employee_id, "folder": folder},
    ).scalar()

    return {"folder": folder, "total": total, "emails": emails}


def get_thread(db: Session, thread_id: str) -> List[Dict[str, Any]]:
    """Get all emails in a thread, ordered chronologically."""
    rows = db.execute(
        text("""
            SELECT id, sender_id, subject, body_html, recipients,
                   created_at
            FROM internal_emails
            WHERE thread_id = :thread_id
            ORDER BY created_at ASC
        """),
        {"thread_id": thread_id},
    ).mappings().all()

    return [
        {
            "id": r["id"],
            "sender_id": r["sender_id"],
            "subject": r["subject"],
            "body_html": r["body_html"],
            "recipients": json.loads(r["recipients"]) if r["recipients"] else [],
            "timestamp": datetime.fromisoformat(r["created_at"]).isoformat() if isinstance(r["created_at"], str) and r["created_at"] else None,
        }
        for r in rows
    ]


# ════════════════════════════════════════════════════════════════
#  Directory / Addressing
# ════════════════════════════════════════════════════════════════

def get_employee_directory(
    db: Session,
    search: Optional[str] = None,
    country_code: Optional[str] = None,
    department: Optional[str] = None,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """Search the employee directory — used by the recipient picker
    for both chat and email composition.
    """
    query = """
        SELECT e.id, e.employee_code, e.department, e.position, e.country_code,
               u.full_name, u.email
        FROM employees e
        JOIN users u ON u.id = e.user_id
        WHERE e.employment_status = 'active'
    """
    params: Dict[str, Any] = {"limit": limit}

    if search:
        query += """
            AND (
                u.full_name ILIKE :search
                OR u.email ILIKE :search
                OR e.employee_code ILIKE :search
                OR e.department ILIKE :search
            )
        """
        params["search"] = f"%{search}%"

    if country_code:
        query += " AND e.country_code = :country"
        params["country"] = country_code

    if department:
        query += " AND e.department = :dept"
        params["dept"] = department

    query += " ORDER BY u.full_name ASC LIMIT :limit"

    rows = db.execute(text(query), params).mappings().all()
    return [dict(r) for r in rows]


# ════════════════════════════════════════════════════════════════
#  Helpers
# ════════════════════════════════════════════════════════════════

def _resolve_attachments(db: Session, attachment_ids: List[int]) -> List[Dict[str, Any]]:
    """Resolve attachment records from chat_attachments table."""
    if not attachment_ids:
        return []

    stmt = text("""
        SELECT id, file_name, attachment_type, file_size_bytes, mime_type, file_url,
               thumbnail_url, duration_seconds, waveform_json, is_processed
        FROM chat_attachments
        WHERE id IN :ids
    """).bindparams(__import__("sqlalchemy").bindparam("ids", expanding=True))

    rows = db.execute(stmt, {"ids": tuple(attachment_ids)}).mappings().all()

    return [dict(r) for r in rows]


def _log_comm_event(
    db: Session,
    actor_id: int,
    target_id: Optional[int],
    action: str,
    entity_type: str,
    entity_id: int,
) -> None:
    """Log a communication event to the activity ledger."""
    try:
        from services.employee_activity_logger import log_activity

        # Get employee country
        emp = db.query(Employee).filter(Employee.id == actor_id).first()
        country = emp.country_code if emp else None

        log_activity(
            db=db,
            actor_employee_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id),
            target_employee_id=target_id,
            country_code=country,
        )
    except Exception as e:
        logger.debug("Failed to log comm event (non-critical): %s", e)
