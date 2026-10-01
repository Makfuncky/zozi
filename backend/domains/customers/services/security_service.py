"""Customer security service — 2FA status, session list, session revoke.

Reads the ``UserSession`` and ``MfaFactor`` aggregates (owned by accounts;
read via ``accounts.ports`` per Law 3) and exposes customer-facing helpers.
"""
from __future__ import annotations

from typing import Any, Dict, List

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from domains.accounts.ports import UserSession, MfaFactor
import structlog

logger = structlog.get_logger(__name__)


def _serialize_session(row: UserSession) -> Dict[str, Any]:
    return {
        "id": row.id,
        "user_id": row.user_id,
        "ip_address": row.ip_address,
        "user_agent": row.user_agent,
        "device_fingerprint": row.device_fingerprint,
        "is_active": row.is_active,
        "expires_at": row.expires_at,
        "created_at": row.created_at,
    }


class SecurityService:
    """Service facade for customer security status / session control."""

    def __init__(self, db: Session):
        self.db = db

    def get_security_status(self, user_id: int) -> Dict[str, Any]:
        """Return 2FA enrolment and active-session counts for a user."""
        factors = (
            self.db.query(MfaFactor)
            .filter(
                MfaFactor.user_id == int(user_id),
                MfaFactor.is_deleted.is_(False),
            )
            .all()
        )
        enabled_factors = [f for f in factors if f.enabled]
        active_sessions = (
            self.db.query(UserSession)
            .filter(
                UserSession.user_id == int(user_id),
                UserSession.is_active.is_(True),
                UserSession.is_deleted.is_(False),
            )
            .count()
        )
        return {
            "user_id": int(user_id),
            "two_factor_enabled": len(enabled_factors) > 0,
            "two_factor_factor_count": len(factors),
            "two_factor_factors": [
                {
                    "id": f.id,
                    "type": f.factor_type.value if hasattr(f.factor_type, "value") else f.factor_type,
                    "enabled": f.enabled,
                    "created_at": f.created_at,
                    "last_used_at": f.last_used_at,
                }
                for f in factors
            ],
            "active_sessions": int(active_sessions or 0),
        }

    def list_sessions(self, user_id: int) -> Dict[str, Any]:
        """Return all active sessions for a user (newest first)."""
        rows = (
            self.db.query(UserSession)
            .filter(
                UserSession.user_id == int(user_id),
                UserSession.is_deleted.is_(False),
            )
            .order_by(UserSession.created_at.desc())
            .all()
        )
        return {
            "user_id": int(user_id),
            "items": [_serialize_session(r) for r in rows],
            "total": len(rows),
        }

    def revoke_session(self, user_id: int, session_id: int) -> Dict[str, Any]:
        """Revoke a single user session. Returns a confirmation payload."""
        row = (
            self.db.query(UserSession)
            .filter(
                UserSession.id == int(session_id),
                UserSession.user_id == int(user_id),
            )
            .first()
        )
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found.",
            )
        if not row.is_active:
            return {
                "session_id": int(session_id),
                "revoked": False,
                "detail": "Session already inactive.",
            }
        row.is_active = False
        self.db.add(row)
        try:
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            logger.error(
                "security.revoke_failed",
                user_id=user_id,
                session_id=session_id,
                error=str(exc),
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to revoke session.",
            ) from exc
        return {
            "session_id": int(session_id),
            "revoked": True,
        }
