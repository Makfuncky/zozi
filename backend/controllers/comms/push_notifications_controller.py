"""Push notification controller.

Thin orchestration between the API layer and ``services.comms.push_notifications_service``.
Satisfies CIR2 (routers → controllers → services); all DB writes live in the service.
"""
from __future__ import annotations

from services.comms.push_notifications_service import (
    list_push_tokens as _list_push_tokens,
    register_push_token as _register_push_token,
    unregister_push_token as _unregister_push_token,
)
import structlog
logger = structlog.get_logger(__name__)


def register_push_token(db, payload, current_user) -> dict:
    return _register_push_token(db, payload.token, payload.device_type, current_user)


def unregister_push_token(db, payload, current_user) -> dict:
    return _unregister_push_token(db, payload.token, current_user)


def list_push_tokens(db, current_user) -> list:
    return _list_push_tokens(db, current_user)
