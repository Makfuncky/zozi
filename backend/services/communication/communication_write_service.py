"""Communication write service — DB write operations for communication entities."""

from datetime import datetime

from sqlalchemy.orm import Session

from models import (
    Notification,
    PushNotificationToken,
    VideoRoom,
    EntityChatThread,
    IncidentWarRoom,
    MaskedMessage,
)


def mark_notification_read(db: Session, notification: Notification) -> Notification:
    notification.is_read = True
    notification.read_at = datetime.utcnow()
    db.commit()
    db.refresh(notification)
    return notification


def delete_notification(db: Session, notification: Notification) -> None:
    db.delete(notification)
    db.commit()


def update_notification_read_status(
    db: Session, notifications: list[Notification], read_at: datetime
) -> None:
    for notification in notifications:
        notification.is_read = True
        notification.read_at = read_at
    db.commit()


def create_push_token(
    db: Session,
    user_id: int,
    token: str,
    platform: str,
    device_name: str = None,
) -> PushNotificationToken:
    push_token = PushNotificationToken(
        user_id=user_id,
        token=token,
        platform=platform,
        device_name=device_name,
        is_active=True,
    )
    db.add(push_token)
    db.commit()
    return push_token


def update_push_token(
    db: Session,
    existing_token: PushNotificationToken,
    platform: str,
    device_name: str = None,
) -> PushNotificationToken:
    existing_token.is_active = True
    existing_token.platform = platform
    if device_name:
        existing_token.device_name = device_name
    db.commit()
    return existing_token


def deactivate_push_token(db: Session, token_obj: PushNotificationToken) -> None:
    token_obj.is_active = False
    db.commit()


def create_video_room(
    db: Session,
    room_id: str,
    room_uuid: str,
    name: str,
    created_by: int,
    max_participants: int = 100,
    recording_enabled: bool = False,
) -> VideoRoom:
    room = VideoRoom(
        room_id=room_id,
        room_uuid=room_uuid,
        name=name,
        created_by=created_by,
        max_participants=max_participants,
        recording_enabled=recording_enabled,
        status="active",
    )
    db.add(room)
    db.commit()
    db.refresh(room)
    return room


def create_chat_thread(
    db: Session,
    entity_type: str,
    entity_id: int,
    title: str = None,
) -> EntityChatThread:
    thread = EntityChatThread(
        entity_type=entity_type,
        entity_id=entity_id,
        title=title,
        is_active=True,
    )
    db.add(thread)
    db.commit()
    db.refresh(thread)
    return thread


def create_incident_room(
    db: Session,
    incident_id: str,
    title: str,
    severity: str = "high",
    created_by: int = 0,
    description: str = None,
) -> IncidentWarRoom:
    war_room = IncidentWarRoom(
        incident_id=incident_id,
        title=title,
        severity=severity,
        status="active",
        created_by=created_by,
        context_data=description,
    )
    db.add(war_room)
    db.commit()
    db.refresh(war_room)
    return war_room


def send_masked_message(
    db: Session,
    sender_id: int,
    recipient_ref: str,
    content: str,
) -> MaskedMessage:
    message = MaskedMessage(
        sender_id=sender_id,
        recipient_ref=recipient_ref,
        message_hash=hash(content),
        content=content,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message