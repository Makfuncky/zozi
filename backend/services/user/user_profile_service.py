"""User profile write operations.

Owns the DB write (commit/refresh) for user profile updates. Routers must not
call session.commit()/refresh() directly for this operation (W1).
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from data.models import User
import structlog
logger = structlog.get_logger(__name__)


def save_user_profile(db: Session, user: User, payload) -> User:
    """Apply an already-validated payload to ``user`` and commit the change."""
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(user, k, v)
    db.commit()
    db.refresh(user)
    return user


def admin_bulk_toggle_active(
    db: Session,
    user_ids: list[int],
    country_code: str,
    is_active: bool,
) -> int:
    """Set ``is_active`` for the given users within a country and commit once.

    Returns the number of users actually updated.
    """
    updated = 0
    for uid in user_ids:
        u = (
            db.query(User)
            .filter(User.id == uid, User.country_code == country_code.upper())
            .first()
        )
        if u:
            u.is_active = is_active
            updated += 1
    db.commit()
    return updated
