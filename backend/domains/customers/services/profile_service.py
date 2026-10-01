"""Profile service — real customer profile read/update + completion scoring.

Owns reads/writes against the canonical ``accounts.User`` model (read via
``accounts.ports`` per Law 3) and computes a deterministic profile-completion
score from the populated fields.

Per ARCHITECTURE_DIAGRAM.md Law 3, this service is the only place that
combines cross-domain reads of ``accounts.users`` + customer-side data.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from domains.accounts.ports import User
import structlog

logger = structlog.get_logger(__name__)


_PROFILE_FIELDS: List[str] = [
    "full_name",
    "email",
    "phone",
    "country_code",
    "staff_country_codes",
]


def _serialize_profile(user: User) -> Dict[str, Any]:
    return {
        "user_id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "country_code": user.country_code,
        "is_active": user.is_active,
        "role": user.role,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
    }


class ProfileService:
    """Service facade for customer profile management."""

    def __init__(self, db: Session):
        self.db = db

    def get_profile(self, user_id: int) -> Dict[str, Any]:
        """Return the canonical customer profile for ``user_id``."""
        user = self.db.query(User).filter(User.id == int(user_id)).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )
        return _serialize_profile(user)

    def update_profile(self, user_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Update a small whitelist of profile fields on the user record."""
        user = self.db.query(User).filter(User.id == int(user_id)).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )
        allowed = {"full_name"}
        updates = {k: v for k, v in (payload or {}).items() if k in allowed}
        if not updates:
            return _serialize_profile(user)
        for key, value in updates.items():
            setattr(user, key, value)
        try:
            self.db.add(user)
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            logger.error("profile.update_failed", user_id=user_id, error=str(exc))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update profile.",
            ) from exc
        self.db.refresh(user)
        return _serialize_profile(user)

    def get_profile_completion(self, user_id: int) -> Dict[str, Any]:
        """Calculate a 0-100 profile-completion score and per-field status."""
        user = self.db.query(User).filter(User.id == int(user_id)).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )
        field_status: Dict[str, bool] = {}
        filled = 0
        for field_name in _PROFILE_FIELDS:
            value: Optional[Any] = getattr(user, field_name, None)
            present = value not in (None, "", [])
            field_status[field_name] = present
            if present:
                filled += 1
        total = max(1, len(_PROFILE_FIELDS))
        percent = int(round((filled / total) * 100))
        return {
            "user_id": user.id,
            "percent": percent,
            "filled": filled,
            "total": total,
            "fields": field_status,
        }
