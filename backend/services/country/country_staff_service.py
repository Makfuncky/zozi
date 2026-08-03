"""Country staff assignment router logic, extracted behind the service layer (clears W1).

Each function owns its database session via ``data.db.get_db_context`` so the
router layer never injects or touches a SQLAlchemy session directly.
"""
from typing import Optional

from fastapi import HTTPException, Query

from utils.datetime_utils import utcnow as _utcnow  # noqa: F401  (kept for parity)


def _staff_payload(assignment) -> dict:
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
        "user_name": (user.full_name or user.username) if user else None,
        "user_email": user.email if user else None,
        "user_role": user.role if user else None,
        "avatar_url": user.avatar_url if user else None,
    }


VALID_ROLES = {"country_head", "country_manager", "country_finance", "country_moderator"}


def list_country_staff(code: str, active_only: bool, skip: int, limit: int) -> dict:
    from data.db import get_db_context
    from data.models_country_enhancements import CountryStaffAssignment
    from data.models import CountryConfig

    cc = code.upper()
    with get_db_context() as db:
        country = db.query(CountryConfig).filter(CountryConfig.code == cc).first()
        if not country:
            raise HTTPException(status_code=404, detail="Country not found")
        q = db.query(CountryStaffAssignment).filter(CountryStaffAssignment.country_code == cc)
        if active_only:
            q = q.filter(CountryStaffAssignment.is_active == True)
        assignments = q.offset(skip).limit(limit).all()
        return {
            "country_code": cc,
            "staff": [_staff_payload(a) for a in assignments],
            "total": len(assignments),
        }


def assign_staff_to_country(code: str, body, current_user: dict) -> dict:
    from data.db import get_db_context
    from data.models_country_enhancements import CountryStaffAssignment
    from data.models import User
    from data.services_write_helpers import add_and_flush, commit_and_refresh

    if body.role_in_country not in VALID_ROLES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role. Must be one of: {', '.join(VALID_ROLES)}",
        )
    cc = code.upper()
    with get_db_context() as db:
        country = db.query(CountryConfig).filter(CountryConfig.code == cc).first()
        if not country:
            raise HTTPException(status_code=404, detail="Country not found")
        user = db.query(User).filter(User.id == body.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        existing = db.query(CountryStaffAssignment).filter(
            CountryStaffAssignment.user_id == body.user_id,
            CountryStaffAssignment.country_code == cc,
        ).first()
        if existing:
            existing.role_in_country = body.role_in_country
            existing.is_active = True
            existing.notes = body.notes
            existing.updated_at = _utcnow()
            commit_and_refresh(db, existing)
            return {"message": "Staff assignment updated", "assignment": _staff_payload(existing)}
        assignment = CountryStaffAssignment(
            user_id=body.user_id,
            country_code=cc,
            role_in_country=body.role_in_country,
            notes=body.notes,
            assigned_by=current_user.get("id"),
            is_active=True,
        )
        add_and_flush(db, assignment)
        commit_and_refresh(db, assignment)
        return {"message": "Staff assigned to country", "assignment": _staff_payload(assignment)}


def update_staff_assignment(code: str, assignment_id: int, body) -> dict:
    from data.db import get_db_context
    from data.models_country_enhancements import CountryStaffAssignment
    from data.services_write_helpers import commit_and_refresh

    cc = code.upper()
    with get_db_context() as db:
        assignment = db.query(CountryStaffAssignment).filter(
            CountryStaffAssignment.id == assignment_id,
            CountryStaffAssignment.country_code == cc,
        ).first()
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")
        if body.role_in_country is not None:
            if body.role_in_country not in VALID_ROLES:
                raise HTTPException(status_code=400, detail="Invalid role")
            assignment.role_in_country = body.role_in_country
        if body.is_active is not None:
            assignment.is_active = body.is_active
        if body.notes is not None:
            assignment.notes = body.notes
        assignment.updated_at = _utcnow()
        commit_and_refresh(db, assignment)
        return {"message": "Assignment updated", "assignment": _staff_payload(assignment)}


def remove_staff_from_country(code: str, user_id: int) -> dict:
    from data.db import get_db_context
    from data.models_country_enhancements import CountryStaffAssignment
    from data.services_write_helpers import commit_only

    cc = code.upper()
    with get_db_context() as db:
        assignment = db.query(CountryStaffAssignment).filter(
            CountryStaffAssignment.user_id == user_id,
            CountryStaffAssignment.country_code == cc,
        ).first()
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")
        assignment.is_active = False
        assignment.updated_at = _utcnow()
        commit_only(db)
        return {"message": "Staff removed from country"}


def get_my_assigned_countries(user_id: int, skip: int, limit: int) -> dict:
    from data.db import get_db_context
    from data.models_country_enhancements import CountryStaffAssignment
    from data.models import CountryConfig

    with get_db_context() as db:
        assignments = db.query(CountryStaffAssignment).filter(
            CountryStaffAssignment.user_id == user_id,
            CountryStaffAssignment.is_active == True,
        ).offset(skip).limit(limit).all()
        result = []
        for a in assignments:
            country = db.query(CountryConfig).filter(CountryConfig.code == a.country_code).first()
            result.append({
                "country_code": a.country_code,
                "country_name": country.name if country else a.country_code,
                "flag_url": country.flag_url if country else None,
                "role_in_country": a.role_in_country,
                "assigned_at": a.created_at.isoformat() if a.created_at else None,
            })
        return {"assigned_countries": result, "total": len(result)}


def list_all_staff_assignments(role: Optional[str], active_only: bool, limit: int) -> dict:
    from data.db import get_db_context
    from data.models_country_enhancements import CountryStaffAssignment

    with get_db_context() as db:
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
