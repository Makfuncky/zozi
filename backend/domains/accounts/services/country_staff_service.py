"""Auto-migrated service logic from routers/country_staff.py."""
from __future__ import annotations

from __future__ import annotations

from typing import Optional

from fastapi import Depends, HTTPException, Query

from pydantic import BaseModel, Field

from sqlalchemy.orm import Session

from modules.admin.routers.auth import require_admin
from domains.governance.services.auth_controller_service import get_current_user

from infrastructure.database.database import get_db

from domains.accounts.models.user import User

from domains.country.models.countries import CountryConfig

from domains.country.models.country_enhancements import CountryStaffAssignment

from infrastructure.utils.datetime_utils import utcnow as _utcnow

class StaffAssignBody(BaseModel):
    user_id: int
    role_in_country: str = Field(
        default="country_manager",
        description="One of: country_head, country_manager, country_finance, country_moderator"
    )
    notes: Optional[str] = None

class StaffUpdateBody(BaseModel):
    role_in_country: Optional[str] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None

VALID_ROLES = {"country_head", "country_manager", "country_finance", "country_moderator"}

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

def list_country_staff(code: str, active_only: bool, db: Session, current_user: dict):
    """List all staff assigned to a country."""
    country = db.query(CountryConfig).filter(CountryConfig.code == code.upper()).first()
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")

    q = db.query(CountryStaffAssignment).filter(
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

def assign_staff_to_country(code: str, body: StaffAssignBody, db: Session, current_user: dict):
    """Assign a user to a country with a specific role."""
    require_admin(current_user)

    if body.role_in_country not in VALID_ROLES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role. Must be one of: {', '.join(VALID_ROLES)}"
        )

    country = db.query(CountryConfig).filter(CountryConfig.code == code.upper()).first()
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")

    user = db.query(User).filter(User.id == body.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if already assigned (upsert logic)
    existing = db.query(CountryStaffAssignment).filter(
        CountryStaffAssignment.user_id == body.user_id,
        CountryStaffAssignment.country_code == code.upper(),
    ).first()

    if existing:
        existing.role_in_country = body.role_in_country
        existing.is_active = True
        existing.notes = body.notes
        existing.updated_at = _utcnow()
        db.commit()
        db.refresh(existing)
        return {"message": "Staff assignment updated", "assignment": _staff_payload(existing)}

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
    return {"message": "Staff assigned to country", "assignment": _staff_payload(assignment)}

def update_staff_assignment(code: str, assignment_id: int, body: StaffUpdateBody, db: Session, current_user: dict):
    """Update a staff assignment (role, active status)."""
    require_admin(current_user)

    assignment = db.query(CountryStaffAssignment).filter(
        CountryStaffAssignment.id == assignment_id,
        CountryStaffAssignment.country_code == code.upper(),
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
    db.commit()
    db.refresh(assignment)
    return {"message": "Assignment updated", "assignment": _staff_payload(assignment)}

def remove_staff_from_country(code: str, user_id: int, db: Session, current_user: dict):
    """Remove (deactivate) a user from a country assignment."""
    require_admin(current_user)

    assignment = db.query(CountryStaffAssignment).filter(
        CountryStaffAssignment.user_id == user_id,
        CountryStaffAssignment.country_code == code.upper(),
    ).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    assignment.is_active = False
    assignment.updated_at = _utcnow()
    db.commit()
    return {"message": "Staff removed from country"}

def get_my_assigned_countries(db: Session, current_user: dict):
    """Get all countries the current user is assigned to."""
    user_id = current_user.get("id")
    assignments = db.query(CountryStaffAssignment).filter(
        CountryStaffAssignment.user_id == user_id,
        CountryStaffAssignment.is_active == True,
    ).all()

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

def list_all_staff_assignments(role: Optional[str], active_only: bool, limit: int, db: Session, current_user: dict):
    """Admin-only: list all staff assignments across all countries."""
    require_admin(current_user)

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


