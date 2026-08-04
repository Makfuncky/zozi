"""Enterprise Communication Controller for Video, Chat, and Email."""
from __future__ import annotations

from services.communication.communication_write_service import (
    create_video_room as create_video_room_svc,
    create_chat_thread as create_chat_thread_svc,
    send_masked_message as send_masked_message_svc,
    create_incident_room as create_incident_room_svc,
)
from services.communication.communication_read_service import (
    get_command_center_metrics as get_command_center_metrics_svc,
)


def create_video_room(room_data: dict, db) -> dict:
    """Create a secure video conference room."""
    import uuid
    from utils.datetime_utils import utcnow

    room_id = str(uuid.uuid4())
    room_uuid = f"room_{uuid.uuid4().hex[:8]}"

    room = create_video_room_svc(
        db=db,
        room_id=room_id,
        room_uuid=room_uuid,
        name=room_data.get("title"),
        created_by=room_data.get("created_by"),
        max_participants=room_data.get("max_participants", 100),
        recording_enabled=False,
    )

    return {"room_id": room.room_id, "room_uuid": room.room_uuid, "invite_link": f"/meet/{room.room_uuid}"}


def create_chat_thread(thread_data: dict, db) -> dict:
    """Create an entity-attached chat thread."""
    thread = create_chat_thread_svc(
        db=db,
        entity_type=thread_data.get("entity_type"),
        entity_id=thread_data.get("entity_id"),
        title=thread_data.get("title"),
    )

    return {"thread_id": thread.id, "invite_code": thread_data.get("entity_id")}


def send_masked_message(sender_id: int, recipient_ref: str, message: str, db) -> dict:
    """Send a masked communication message."""
    send_masked_message_svc(
        db=db,
        sender_id=sender_id,
        recipient_ref=recipient_ref,
        content=message,
    )

    return {"status": "sent", "recipient": recipient_ref}


def create_incident_room(alert_data: dict, db) -> dict:
    """Create an incident command room for critical alerts."""
    room = create_incident_room_svc(
        db=db,
        incident_id=alert_data.get("title"),
        title=alert_data.get("title"),
        severity=alert_data.get("severity", "high"),
        created_by=alert_data.get("created_by", 0),
        description=alert_data.get("description"),
    )

    return {"room_id": room.id, "status": "created", "severity": alert_data.get("severity")}


def get_command_center_metrics(db) -> dict:
    """Get real-time command center metrics."""
    return get_command_center_metrics_svc(db)

