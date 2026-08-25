"""Session (UserSession) management for the accounts domain."""
from __future__ import annotations

import logging
from typing import List, Optional

from sqlalchemy.orm import Session

from domains.governance.models.core import UserSession
from infrastructure.utils.performance_cache import cache_session, set_session, invalidate_session
from infrastructure.observability.service_observability import (
    db_query_timer,
    get_correlation_id,
    log_service_call,
    log_service_error,
    request_context,
)

logger = logging.getLogger(__name__)

_SESSION_CACHE_TTL = 300  # 5 minutes


def list_sessions(user_id: int, db: Session) -> List[UserSession]:
    with request_context(user_id=str(user_id)):
        log_service_call("session_service", "list_sessions", user_id=user_id)
        try:
            with db_query_timer("select_user_sessions"):
                result = (
                    db.query(UserSession)
                    .filter(UserSession.user_id == user_id, UserSession.is_active.is_(True))
                    .order_by(UserSession.last_activity.desc())
                    .all()
                )
            log_service_call("session_service", "list_sessions", level="debug", result_count=len(result))
            return result
        except Exception as exc:
            log_service_error("session_service", "list_sessions", exc, user_id=user_id)
            raise


def get_session_by_token(session_token: str, db: Session) -> Optional[UserSession]:
    """Look up a session by token with Redis cache fallback."""
    cached = cache_session(session_token)
    if cached is not None:
        return cached  # type: ignore[return-value]

    try:
        with db_query_timer("select_session_by_token"):
            session = (
                db.query(UserSession)
                .filter(UserSession.session_token == session_token, UserSession.is_active.is_(True))
                .first()
            )
        if session is not None:
            set_session(
                session_token,
                {
                    "id": session.id,
                    "user_id": session.user_id,
                    "is_active": session.is_active,
                    "country_code": session.country_code,
                },
                ttl=_SESSION_CACHE_TTL,
            )
        return session
    except Exception as exc:
        log_service_error("session_service", "get_session_by_token", exc)
        raise


def revoke_session(user_id: int, session_id: int, db: Session) -> bool:
    with request_context(user_id=str(user_id)):
        log_service_call("session_service", "revoke_session", user_id=user_id, session_id=session_id)
        try:
            with db_query_timer("select_user_session"):
                session = (
                    db.query(UserSession)
                    .filter(UserSession.id == session_id, UserSession.user_id == user_id)
                    .first()
                )
            if session is None:
                log_service_call("session_service", "revoke_session", level="warning", result="not_found")
                return False
            session.is_active = False
            db.commit()
            invalidate_session(session.session_token)
            log_service_call("session_service", "revoke_session", level="info", result="revoked")
            return True
        except Exception as exc:
            log_service_error("session_service", "revoke_session", exc, user_id=user_id, session_id=session_id)
            db.rollback()
            raise


def invalidate_user_sessions(user_id: int, db: Session) -> int:
    """Revoke all active sessions for a user and invalidate their cache entries."""
    with request_context(user_id=str(user_id)):
        log_service_call("session_service", "invalidate_user_sessions", user_id=user_id)
        try:
            with db_query_timer("select_active_sessions"):
                sessions = (
                    db.query(UserSession)
                    .filter(UserSession.user_id == user_id, UserSession.is_active.is_(True))
                    .all()
                )
            for session in sessions:
                session.is_active = False
                invalidate_session(session.session_token)
            db.commit()
            log_service_call(
                "session_service", "invalidate_user_sessions",
                level="info", revoked_count=len(sessions),
            )
            return len(sessions)
        except Exception as exc:
            log_service_error("session_service", "invalidate_user_sessions", exc, user_id=user_id)
            db.rollback()
            raise
