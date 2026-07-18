"""
Notifications Controller — notification retrieval, mark-read, and delete logic.
"""
from datetime import datetime
from typing import List

from fastapi import HTTPException
from sqlalchemy.orm import Session

from models import Notification, PushNotificationToken
from utils.constants import NOTIFICATIONS_PAGE_LIMIT


def get_notifications(current_user: dict, db: Session) -> List[Notification]:
    return (
        db.query(Notification)
        .filter(Notification.user_id == current_user["id"])
        .order_by(Notification.created_at.desc())
        .limit(NOTIFICATIONS_PAGE_LIMIT)
        .all()
    )


def mark_all_read(current_user: dict, db: Session) -> dict:
    unread_notifications = (
        db.query(Notification)
        .filter(
            Notification.user_id == current_user["id"],
            Notification.is_read == False,
        )
        .all()
    )
    for notification in unread_notifications:
        notification.is_read = True
        notification.read_at = datetime.utcnow()
    db.commit()
    return {"detail": "All notifications marked as read"}


def mark_notification_read(notification_id: int, current_user: dict, db: Session) -> Notification:
    notif = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user["id"],
    ).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    notif.is_read = True
    notif.read_at = datetime.utcnow()
    db.commit()
    db.refresh(notif)
    return notif


def delete_notification(notification_id: int, current_user: dict, db: Session) -> dict:
    notif = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user["id"],
    ).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    db.delete(notif)
    db.commit()
    return {"detail": "Notification deleted"}


# ── Push Token Handshake ───────────────────────────────────────────────────────

def register_push_token(token: str, platform: str, device_name: str | None, current_user: dict, db: Session) -> dict:
    """Register (or re-activate) a push notification token for the current user."""
    if not token or not token.strip():
        raise HTTPException(status_code=422, detail="token is required")
    token = token.strip()
    allowed_platforms = {"expo", "fcm", "apns"}
    if platform not in allowed_platforms:
        raise HTTPException(status_code=422, detail=f"platform must be one of {sorted(allowed_platforms)}")

    user_id = int(current_user["id"])
    existing = db.query(PushNotificationToken).filter(
        PushNotificationToken.user_id == user_id,
        PushNotificationToken.token == token,
    ).first()

    if existing:
        existing.is_active = True
        existing.platform = platform
        if device_name:
            existing.device_name = device_name
        db.commit()
        return {"detail": "Push token updated", "status": "updated", "token": token}

    push_token = PushNotificationToken(
        user_id=user_id,
        token=token,
        platform=platform,
        device_name=device_name,
        is_active=True,
    )
    db.add(push_token)
    db.commit()
    return {"detail": "Push token registered", "status": "registered", "token": token}


def unregister_push_token(token: str, current_user: dict, db: Session) -> dict:
    """Deactivate a push notification token (e.g. on logout)."""
    user_id = int(current_user["id"])
    row = db.query(PushNotificationToken).filter(
        PushNotificationToken.user_id == user_id,
        PushNotificationToken.token == token,
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="Push token not found")
    row.is_active = False
    db.commit()
    return {"detail": "Push token unregistered", "status": "unregistered", "token": token}

