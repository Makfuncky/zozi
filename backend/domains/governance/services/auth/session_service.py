"""Session (UserSession) management for the accounts domain."""
from __future__ import annotations

from typing import List

from sqlalchemy.orm import Session

from domains.governance.models.core import UserSession


def list_sessions(user_id: int, db: Session) -> List[UserSession]:
    return (
        db.query(UserSession)
        .filter(UserSession.user_id == user_id, UserSession.is_active.is_(True))
        .order_by(UserSession.last_activity.desc())
        .all()
    )


def revoke_session(user_id: int, session_id: int, db: Session) -> bool:
    session = (
        db.query(UserSession)
        .filter(UserSession.id == session_id, UserSession.user_id == user_id)
        .first()
    )
    if session is None:
        return False
    session.is_active = False
    db.commit()
    return True
