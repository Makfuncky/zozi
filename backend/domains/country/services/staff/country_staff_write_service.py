"""Country staff write + read operations.

Owns every DB read and write for the country-staff router so the router layer
stays a thin HTTP adapter. Functions take the injected ``db`` session (the
router's ``Depends(get_db)``) and own ``add``/``commit``/``refresh`` (W1), and
also own the queries that previously lived in the router (Q1).

Return shapes are intentionally identical to the previous router implementation
so existing API clients are unaffected.
"""
from __future__ import annotations

from typing import Any, Optional

from sqlalchemy.orm import Session, joinedload

from domains.country.models.countries import CountryConfig
from domains.country.models.country_enhancements import CountryStaffAssignment
from infrastructure.utils.datetime_utils import utcnow as _utcnow
import structlog
logger = structlog.get_logger(__name__)


def _staff_payload(assignment: CountryStaffAssignment) -> dict:
    user = assignment.user
    return {
        "id": assignment.id,
        "user_id": assignment.user_id,
        "country_code": assignment.country_code,
        "role_in_country": assignment.role_in_country,
        "is_active": assignment.is_active,
        "notes": assignment.notes,
        "assigned_at": assignment.created_at.isoformat() if assignment.created_at else None,
        "updated_at": assignment.updated_at.isoformat() if assignment.updated_at else None,
        # User info
        "user_name": (user.full_name or user.username) if user else None,
        "user_email": user.email if user else None,
        "user_role": user.role if user else None,
        "avatar_url": user.avatar_url if user else None,
    }


def list_country_staff(db: Session, code: str, active_only: bool = True) -> dict:
    """List all staff assigned to a country (Q1: read moved out of router)."""
    country = db.query(CountryConfig).filter(CountryConfig.code == code.upper()).first()
    if not country:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Country not found")

    q = db.query(CountryStaffAssignment).options(
        joinedload(CountryStaffAssignment.user)
    ).filter(
        CountryStaffAssignment.country_code == code.upper()
    )
    if active_only:
        q = q.filter(CountryStaffAssignment.is_active == True)

    assignments = q.all()
    return {
        "country_code": code.upper(),
        "staff": [_staff_payload(a) for a in assignments],
        "total": len(assignments),
    }


def upsert_staff_assignment(
    db: Session, code: str, body: Any, current_user: dict
) -> dict:
    """Assign a user to a country with a specific role (upsert on existing)."""
    country = db.query(CountryConfig).filter(CountryConfig.code == code.upper()).first()
    if not country:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Country not found")

    user = db.query(User).filter(User.id == body.user_id).first()
    if not user:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="User not found")

    existing = (
        db.query(CountryStaffAssignment)
        .filter(
            CountryStaffAssignment.user_id == body.user_id,
            CountryStaffAssignment.country_code == code.upper(),
        )
        .first()
    )

    if existing:
        existing.role_in_country = body.role_in_country
        existing.is_active = True
        existing.notes = body.notes
        existing.updated_at = _utcnow()
        db.commit()
        db.refresh(existing)
        return {
            "message": "Staff assignment updated",
            "assignment": _staff_payload(existing),
        }

    assignment = CountryStaffAssignment(
        user_id=body.user_id,
        country_code=code.upper(),
        role_in_country=body.role_in_country,
        notes=body.notes,
        assigned_by=current_user.get("id"),
        is_active=True,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return {
        "message": "Staff assigned to country",
        "assignment": _staff_payload(assignment),
    }


def update_staff_assignment(
    db: Session, code: str, assignment_id: int, body: Any
) -> dict:
    """Update a staff assignment (role, active status, notes)."""
    assignment = (
        db.query(CountryStaffAssignment)
        .filter(
            CountryStaffAssignment.id == assignment_id,
            CountryStaffAssignment.country_code == code.upper(),
        )
        .first()
    )
    if not assignment:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Assignment not found")

    if body.role_in_country is not None:
        assignment.role_in_country = body.role_in_country
    if body.is_active is not None:
        assignment.is_active = body.is_active
    if body.notes is not None:
        assignment.notes = body.notes

    assignment.updated_at = _utcnow()
    db.commit()
    db.refresh(assignment)
    return {
        "message": "Assignment updated",
        "assignment": _staff_payload(assignment),
    }


def remove_staff_from_country(db: Session, code: str, user_id: int) -> dict:
    """Remove (deactivate) a user from a country assignment."""
    assignment = (
        db.query(CountryStaffAssignment)
        .filter(
            CountryStaffAssignment.user_id == user_id,
            CountryStaffAssignment.country_code == code.upper(),
        )
        .first()
    )
    if not assignment:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Assignment not found")

    try:
        assignment.is_active = False
        assignment.updated_at = _utcnow()
        db.commit()
        return {"message": "Staff removed from country"}
    except Exception:
        db.rollback()
        raise


def get_my_assigned_countries(db: Session, user_id: int) -> dict:
    """Get all countries the given user is assigned to."""
    assignments = (
        db.query(CountryStaffAssignment)
        .filter(
            CountryStaffAssignment.user_id == user_id,
            CountryStaffAssignment.is_active == True,
        )
        .all()
    )

    result = []
    for a in assignments:
        country = (
            db.query(CountryConfig).filter(CountryConfig.code == a.country_code).first()
        )
        result.append(
            {
                "country_code": a.country_code,
                "country_name": country.name if country else a.country_code,
                "flag_url": country.flag_url if country else None,
                "role_in_country": a.role_in_country,
                "assigned_at": a.created_at.isoformat() if a.created_at else None,
            }
        )

    return {"assigned_countries": result, "total": len(result)}


def list_all_staff_assignments(
    db: Session,
    role: Optional[str] = None,
    active_only: bool = True,
    limit: int = 100,
) -> dict:
    """Admin-only: list all staff assignments across all countries."""
    q = db.query(CountryStaffAssignment)
    if active_only:
        q = q.filter(CountryStaffAssignment.is_active == True)
    if role:
        q = q.filter(CountryStaffAssignment.role_in_country == role)

    assignments = q.limit(limit).all()
    return {
        "assignments": [_staff_payload(a) for a in assignments],
        "total": len(assignments),
    }

# === Merged from country_staff_service.py ===
# Read-side functions preserved for reference
