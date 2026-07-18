from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from models import AuditLog

logger = logging.getLogger(__name__)

SECURITY_EVENTS = frozenset({
    "LOGIN_SUCCESS",
    "LOGIN_FAILED",
    "LOGIN_BLOCKED",
    "LOGOUT",
    "2FA_ENABLED",
    "2FA_DISABLED",
    "2FA_VERIFIED",
    "2FA_FAILED",
    "TOTP_SETUP",
    "PASSWORD_CHANGE",
    "PASSWORD_RESET_REQUEST",
    "PASSWORD_RESET_COMPLETED",
    "ACCOUNT_LOCKED",
    "ACCOUNT_UNLOCKED",
    "SESSION_REVOKED",
    "SESSION_EXPIRED",
    "IMPOSSIBLE_TRAVEL_DETECTED",
    "NEW_DEVICE_DETECTED",
    "TOKEN_REFRESH",
    "TOKEN_REUSE_DETECTED",
    "PAYOUT_CREATED",
    "PAYOUT_APPROVED",
    "PAYOUT_REJECTED",
    "PAYOUT_RELEASED",
    "PAYOUT_FAILED",
    "WEBHOOK_RECEIVED",
    "WEBHOOK_VERIFIED",
    "WEBHOOK_FAILED",
    "WEBHOOK_REPLAYED",
    "RLS_VIOLATION_ATTEMPT",
    "RATE_LIMIT_EXCEEDED",
    "ADMIN_ACTION",
    "PERMISSION_CHANGE",
    "COUNTRY_CONFIG_CHANGE",
    "API_KEY_CREATED",
    "API_KEY_REVOKED",
    "SUSPICIOUS_ACTIVITY",
    "GHOST_ORDER_DETECTED",
})


def log_security_event(
    action: str,
    user_id: int | None = None,
    username: str | None = None,
    user_role: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    details: dict[str, Any] | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    status: str = "success",
) -> int | None:
    if action not in SECURITY_EVENTS:
        logger.warning("Unknown security event type: %s", action)

    from db.database import get_service_session
    try:
        with get_service_session() as db:
            entry = AuditLog(
                user_id=user_id,
                username=username,
                user_role=user_role,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details=json.dumps(details) if details else None,
                ip_address=ip_address,
                user_agent=user_agent,
                status=status,
            )
            db.add(entry)
            db.refresh(entry)
            return entry.id
    except Exception as exc:
        logger.error("Failed to write audit log: %s", exc)
        return None

