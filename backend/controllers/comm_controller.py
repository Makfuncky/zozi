"""Enterprise Communication Controller for Video, Chat, and Email."""
from __future__ import annotations
import uuid
from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from models.employee_models import Employee
from utils.datetime_utils import utcnow as _utcnow


def create_video_room(room_data: dict, db: Session) -> dict:
    """Create a secure video conference room."""
    room_id = str(uuid.uuid4())
    room_uuid = f"room_{uuid.uuid4().hex[:8]}"
    now = _utcnow()

    db.execute(text("""
        INSERT INTO video_rooms
            (room_id, room_uuid, name, created_by, max_participants,
             recording_enabled, status, created_at, updated_at)
        VALUES (:room_id, :room_uuid, :name, :creator, :max_p,
                :recording, :status, :created, :updated)
    """), {
        "room_id": room_id,
        "room_uuid": room_uuid,
        "name": room_data.get("title"),
        "creator": room_data.get("created_by"),
        "max_p": room_data.get("max_participants", 100),
        "recording": False,
        "status": "active",
        "created": now,
        "updated": now,
    })
    db.commit()

    return {"room_id": room_id, "room_uuid": room_uuid, "invite_link": f"/meet/{room_uuid}"}


def create_chat_thread(thread_data: dict, db: Session) -> dict:
    """Create an entity-attached chat thread."""
    now = _utcnow()
    db.execute(text("""
        INSERT INTO entity_chat_threads (entity_type, entity_id, title, is_active, created_at, updated_at)
        VALUES (:etype, :eid, :title, :active, :created, :updated)
    """), {
        "etype": thread_data.get("entity_type"),
        "eid": thread_data.get("entity_id"),
        "title": thread_data.get("title"),
        "active": True,
        "created": now,
        "updated": now,
    })
    thread_id = db.execute(text("SELECT last_insert_rowid()")).scalar()
    db.commit()

    return {"thread_id": thread_id, "invite_code": thread_data.get("entity_id")}


def send_masked_message(sender_id: int, recipient_ref: str, message: str, db: Session) -> dict:
    """Send a masked communication message."""
    db.execute(text("""
        INSERT INTO masked_messages (sender_id, recipient_ref, message_hash, content, sent_at)
        VALUES (:sender, :recipient, :msg_hash, :content, :now)
    """), {
        "sender": sender_id,
        "recipient": recipient_ref,
        "msg_hash": hash(message),
        "content": message,
        "now": _utcnow(),
    })
    db.commit()

    return {"status": "sent", "recipient": recipient_ref}


def create_incident_room(alert_data: dict, db: Session) -> dict:
    """Create an incident command room for critical alerts."""
    room_id = f"incident_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    now = _utcnow()

    db.execute(text("""
        INSERT INTO incident_war_rooms
            (incident_id, title, severity, status, started_at, created_by, context_data)
        VALUES (:rid, :title, :sev, :status, :started, :creator, :ctx)
    """), {
        "rid": room_id,
        "title": alert_data.get("title"),
        "sev": alert_data.get("severity", "high"),
        "status": "active",
        "started": now,
        "creator": alert_data.get("created_by", 0),
        "ctx": alert_data.get("description"),
    })
    db.commit()

    return {"room_id": room_id, "status": "created", "severity": alert_data.get("severity")}


def get_command_center_metrics(db: Session) -> dict:
    """Get real-time command center metrics."""
    metrics = db.execute(text("""
        SELECT
            (SELECT COUNT(*) FROM employees WHERE employment_status = 'active') as active_employees,
            (SELECT COUNT(*) FROM employee_attendance WHERE date = CURRENT_DATE) as today_attendance,
            (SELECT COUNT(*) FROM video_rooms WHERE created_at >= CURRENT_DATE) as active_rooms,
            (SELECT COUNT(*) FROM entity_chat_threads) as total_threads
    """)).fetchone()

    return {
        "active_employees": metrics[0] or 0,
        "today_attendance": metrics[1] or 0,
        "active_meeting_rooms": metrics[2] or 0,
        "active_chat_threads": metrics[3] or 0,
        "last_updated": _utcnow().isoformat(),
    }

