"""
Push Notification Token Router — register/unregister mobile push tokens.
Supports Expo Push, FCM, and APNs tokens.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timezone

from db.database import get_db
from models import PushNotificationToken
from routers.auth import get_current_user

from services.write_helpers import add_and_flush, commit_only, delete_only
router = APIRouter()


def _user_id(user: object) -> int:
    if hasattr(user, "id"):
        return int(getattr(user, "id") or 0)
    if isinstance(user, dict):
        return int(user.get("id") or 0)
    return 0


class PushTokenRegister(BaseModel):
    token: str
    device_type: Optional[str] = None


@router.post("/register")
def register_push_token(
    payload: PushTokenRegister,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Register or refresh a push notification token for the current user."""
    user_id = _user_id(current_user)

    existing = (
        db.query(PushNotificationToken)
        .filter(
            PushNotificationToken.user_id == user_id,
            PushNotificationToken.token == payload.token,
        )
        .first()
    )

    if existing:
        existing.device_type = payload.device_type
        existing.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        commit_only(db)
        return {"status": "updated"}

    record = PushNotificationToken(
        user_id=user_id,
        token=payload.token,
        device_type=payload.device_type,
    )
    add_and_flush(db, record)
    commit_only(db)
    return {"status": "registered"}


@router.delete("/unregister")
def unregister_push_token(
    payload: PushTokenRegister,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Deactivate a push token (e.g. on logout or permission withdrawal)."""
    user_id = _user_id(current_user)
    record = (
        db.query(PushNotificationToken)
        .filter(
            PushNotificationToken.user_id == user_id,
            PushNotificationToken.token == payload.token,
        )
        .first()
    )
    if record:
        delete_only(db, record)
        commit_only(db)
    return {"status": "unregistered"}


@router.get("")
def list_push_tokens(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List all active push tokens for the current user (for debugging)."""
    user_id = _user_id(current_user)
    tokens = (
        db.query(PushNotificationToken)
        .filter(
            PushNotificationToken.user_id == user_id,
        )
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
