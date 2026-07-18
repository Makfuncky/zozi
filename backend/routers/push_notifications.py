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

router = APIRouter()


class PushTokenRegister(BaseModel):
    token: str
    platform: str = "expo"  # expo | fcm | apns
    device_name: Optional[str] = None


@router.post("/register")
def register_push_token(
    payload: PushTokenRegister,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Register or refresh a push notification token for the current user."""
    user_id = current_user["id"]

    existing = (
        db.query(PushNotificationToken)
        .filter(
            PushNotificationToken.user_id == user_id,
            PushNotificationToken.token == payload.token,
        )
        .first()
    )

    if existing:
        existing.is_active = True
        existing.platform = payload.platform
        existing.device_name = payload.device_name
        existing.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db.commit()
        return {"status": "updated"}

    record = PushNotificationToken(
        user_id=user_id,
        token=payload.token,
        platform=payload.platform,
        device_name=payload.device_name,
        is_active=True,
    )
    db.add(record)
    db.commit()
    return {"status": "registered"}


@router.delete("/unregister")
def unregister_push_token(
    payload: PushTokenRegister,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Deactivate a push token (e.g. on logout or permission withdrawal)."""
    user_id = current_user["id"]
    record = (
        db.query(PushNotificationToken)
        .filter(
            PushNotificationToken.user_id == user_id,
            PushNotificationToken.token == payload.token,
        )
        .first()
    )
    if record:
        record.is_active = False
        db.commit()
    return {"status": "unregistered"}


@router.get("")
def list_push_tokens(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List all active push tokens for the current user (for debugging)."""
    tokens = (
        db.query(PushNotificationToken)
        .filter(
            PushNotificationToken.user_id == current_user["id"],
            PushNotificationToken.is_active == True,
        )
        .all()
    )
    return [
        {
            "id": t.id,
            "platform": t.platform,
            "device_name": t.device_name,
            "created_at": t.created_at,
        }
        for t in tokens
    ]

