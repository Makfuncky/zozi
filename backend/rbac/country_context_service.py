"""Country / RLS resolution service.

Holds the DB-backed logic that the country-context middleware previously
performed inline (querying ``CountryStaffAssignment`` / ``User`` directly).
Keeping it here makes the middleware a thin request-time coordinator and the
ORM access lives in the service layer, matching the rest of the codebase.
"""
from __future__ import annotations

from typing import Optional, Set

from sqlalchemy.orm import Session

from models import CountryStaffAssignment, User


def resolve_user_country_scope(user, db: Session) -> Set[str]:
    """Resolve the set of country codes a user is allowed to access."""
    if getattr(user, "role", None) in {"admin", "super_admin"}:
        return set()

    assignments = (
        db.query(CountryStaffAssignment.country_code)
        .filter(
            CountryStaffAssignment.user_id == user.id,
            CountryStaffAssignment.is_active == True,  # noqa: E712
        )
        .all()
    )

    codes = {str(row[0]).upper().strip() for row in assignments if row[0]}
    return codes


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Fetch a user by primary key."""
    return db.query(User).filter(User.id == user_id).first()
