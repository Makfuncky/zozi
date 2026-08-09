"""Enterprise Communication Controller for Video, Chat, and Email."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.orm import Session

from utils.datetime_utils import utcnow as _utcnow
from services.communication_write_service import (
    create_video_room as _create_video_room,
    create_chat_thread as _create_chat_thread,
    create_incident_room as _create_incident_room,
    send_masked_message as _send_masked_message,
)


def create_video_room(room_data: dict, db: Session) -> dict:
    """Create a secure video conference room."""
    room_id = str(uuid.uuid4())
    room_uuid = f"room_{uuid.uuid4().hex[:8]}"
    
    _create_video_room(
        db=db,
        room_id=room_id,
        room_uuid=room_uuid,
        name=room_data.get("title"),
        created_by=room_data.get("created_by"),
        max_participants=room_data.get("max_participants", 100),
        recording_enabled=False,
    )

    return {"room_id": room_id, "room_uuid": room_uuid, "invite_link": f"/meet/{room_uuid}"}


def create_chat_thread(thread_data: dict, db: Session) -> dict:
    """Create an entity-attached chat thread."""
    thread = _create_chat_thread(
        db=db,
        entity_type=thread_data.get("entity_type"),
        entity_id=thread_data.get("entity_id"),
        title=thread_data.get("title"),
    )

    return {"thread_id": thread.id, "invite_code": thread_data.get("entity_id")}


def send_masked_message(sender_id: int, recipient_ref: str, message: str, db: Session) -> dict:
    """Send a masked communication message."""
    _send_masked_message(
        db=db,
        sender_id=sender_id,
        recipient_ref=recipient_ref,
        content=message,
    )

    return {"status": "sent", "recipient": recipient_ref}


def create_incident_room(alert_data: dict, db: Session) -> dict:
    """Create an incident command room for critical alerts."""
    room_id = f"incident_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    
    _create_incident_room(
        db=db,
        incident_id=room_id,
        title=alert_data.get("title"),
        severity=alert_data.get("severity", "high"),
        created_by=alert_data.get("created_by", 0),
        description=alert_data.get("description"),
    )

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