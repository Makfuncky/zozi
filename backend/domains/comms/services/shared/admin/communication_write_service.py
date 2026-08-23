"""Communication write service — DB write operations for communication entities."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from domains.governance.ports import PushNotificationToken
from domains.comms.models.communication import MaskedMessage
from domains.comms.models.communication import Notification
from domains.governance.ports import EntityChatThread
from domains.governance.ports import VideoRoom
from domains.governance.ports import IncidentWarRoom
import structlog
logger = structlog.get_logger(__name__)

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

