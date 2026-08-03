"""
Push Notification Token Router â€” register/unregister mobile push tokens.
Supports Expo Push, FCM, and APNs tokens.
"""
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from typing import Optional

from data.dependencies_auth import get_current_user
from data.services_communication_push_notifications_service import (
    register_push_token,
    unregister_push_token,
    list_push_tokens,
)

router = APIRouter()


class PushTokenRegister(BaseModel):
    token: str
    device_type: Optional[str] = None


@router.post("/register")
def register(
    payload: PushTokenRegister,
    current_user: dict = Depends(get_current_user),
):
    """Register or refresh a push notification token for the current user."""
    return register_push_token(payload.token, payload.device_type, current_user)


@router.delete("/unregister")
def unregister(
    payload: PushTokenRegister,
    current_user: dict = Depends(get_current_user),
):
    """Deactivate a push token (e.g. on logout or permission withdrawal)."""
    return unregister_push_token(payload.token, current_user)


@router.get("")
def list_tokens(
    current_user: dict = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    """List all active push tokens for the current user (for debugging)."""
    return list_push_tokens(current_user, skip, limit)
