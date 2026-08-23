"""User profile read service (W1 transaction/scope owner for user lookups).

Centralises display-name and role resolution so chat/notification code no
longer reaches into the ORM from controllers.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from domains.accounts.models.user import User
import structlog

logger = structlog.get_logger(__name__)


def get_user_display_name(db: Session, user_id: int) -> str:
    """Return a human-readable display name for a user id."""
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        return f"User {user_id}"
    name = getattr(user, "full_name", None) or getattr(user, "display_name", None)
    if name:
        return name
    email = getattr(user, "email", None)
    return email or f"User {user_id}"


def get_user_role(db: Session, user_id: int) -> str:
    """Return the role string for a user id."""
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        return "unknown"
    return getattr(user, "role", "unknown") or "unknown"
