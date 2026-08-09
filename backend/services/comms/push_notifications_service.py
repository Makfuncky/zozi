"""Push notification token service.

Owns the DB writes for push-token registration. Functions receive the active
SQLAlchemy ``Session`` from the caller (the router/controller dependency) so no
session is opened or closed here — this keeps the router circuit clean (W1)
while staying testable.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from data.models import PushNotificationToken
import structlog
logger = structlog.get_logger(__name__)


def _user_id(user: object) -> int:
    if hasattr(user, "id"):
        return int(getattr(user, "id") or 0)
    if isinstance(user, dict):
        return int(user.get("id") or 0)
    return 0


def register_push_token(db: Session, token: str, device_type: Optional[str], current_user) -> dict:
    """Register or refresh a push notification token for the current user."""
    user_id = _user_id(current_user)
    existing = (
        db.query(PushNotificationToken)
        .filter(
            PushNotificationToken.user_id == user_id,
            PushNotificationToken.token == token,
        )
        .first()
    )
    if existing:
        existing.device_type = device_type
        existing.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db.commit()
        return {"status": "updated"}

    record = PushNotificationToken(
        user_id=user_id,
        token=token,
        device_type=device_type,
    )
    db.add(record)
    db.commit()
    return {"status": "registered"}


def unregister_push_token(db: Session, token: str, current_user) -> dict:
    """Deactivate a push token for the current user."""
    user_id = _user_id(current_user)
    record = (
        db.query(PushNotificationToken)
        .filter(
            PushNotificationToken.user_id == user_id,
            PushNotificationToken.token == token,
        )
        .first()
    )
    if record:
        db.delete(record)
        db.commit()
    return {"status": "unregistered"}


def list_push_tokens(db: Session, current_user) -> list:
    """List all push tokens for the current user."""
    user_id = _user_id(current_user)
    tokens = (
        db.query(PushNotificationToken)
        .filter(PushNotificationToken.user_id == user_id)
        .all()
    )
    return [
        {
            "id": t.id,
            "device_type": t.device_type,
            "created_at": t.created_at,
        }
        for t in tokens
    ]
