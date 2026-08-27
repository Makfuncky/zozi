"""Country / RLS resolution service.

Holds the DB-backed logic that the country-context middleware previously
performed inline (querying ``CountryStaffAssignment`` / ``User`` directly).
Keeping it here makes the middleware a thin request-time coordinator and the
ORM access lives in the service layer, matching the rest of the codebase.
"""
from __future__ import annotations

from typing import Set

from sqlalchemy.orm import Session

from domains.country.models.country_enhancements import CountryStaffAssignment
from domains.accounts.ports import get_user_by_id


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
