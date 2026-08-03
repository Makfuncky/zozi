"""
Notification Engine API Endpoints
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from data.db import get_db
from data.dependencies_auth import get_current_user
from services.notification_engine import get_notification_engine, NotificationChannel, NotificationPriority

router = APIRouter()


def _parse_channel(value: str) -> NotificationChannel:
    try:
        return NotificationChannel(value)
    except ValueError:
        return NotificationChannel.IN_APP


def _parse_priority(value: str) -> NotificationPriority:
    try:
        return NotificationPriority(value)
    except ValueError:
        return NotificationPriority.MEDIUM


@router.post("/send")
def send_notification(
    user_id: int,
    title: str,
    message: str,
    channel: str = "in_app",
    priority: str = "medium",
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    engine = get_notification_engine(db)
    return engine.send(user_id, title, message, _parse_channel(channel), _parse_priority(priority))


@router.post("/bulk")
def send_bulk_notifications(
    user_ids: list,
    title: str,
    message: str,
    channel: str = "email",
    priority: str = "medium",
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    engine = get_notification_engine(db)
    return engine.send_bulk(user_ids, title, message, _parse_channel(channel), _parse_priority(priority))


@router.get("")
def get_notifications(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    unread_only: bool = False,
):
    user_id = current_user.get("id")
    engine = get_notification_engine(db)
    return engine.get_user_notifications(user_id, unread_only)


@router.post("/{notification_id}/read")
def mark_notification_read(
    notification_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_id = current_user.get("id")
    engine = get_notification_engine(db)
    return engine.mark_read(notification_id, user_id)
