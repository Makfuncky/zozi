"""
Country Staff Assignments Router
Handles assigning/removing users as country_head, country_manager, etc.
"""
from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from dependencies.auth import get_current_user
from controllers.admin_controller import require_admin
from db.database import get_db
from models.country_enhancements import CountryStaffAssignment
from models.countries import CountryConfig
from models import User
from utils.datetime_utils import utcnow as _utcnow

from services.write_helpers import add_and_flush, commit_and_refresh, commit_only
router = APIRouter()


# ─── Schemas ────────────────────────────────────────────────────────────────────

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


# ─── Helpers ────────────────────────────────────────────────────────────────────

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


# ─── Endpoints ──────────────────────────────────────────────────────────────────

@router.get("/countries/{code}/staff")
def list_country_staff(
    code: str,
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
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


@router.post("/countries/{code}/staff")
def assign_staff_to_country(
    code: str,
    body: StaffAssignBody,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
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
        commit_and_refresh(db, existing)
        return {"message": "Staff assignment updated", "assignment": _staff_payload(existing)}

    assignment = CountryStaffAssignment(
        user_id=body.user_id,
        country_code=code.upper(),
        role_in_country=body.role_in_country,
        notes=body.notes,
        assigned_by=current_user.get("id"),
        is_active=True,
    )
    add_and_flush(db, assignment)
    commit_and_refresh(db, assignment)
    return {"message": "Staff assigned to country", "assignment": _staff_payload(assignment)}


@router.patch("/countries/{code}/staff/{assignment_id}")
def update_staff_assignment(
    code: str,
    assignment_id: int,
    body: StaffUpdateBody,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
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
            raise HTTPException(status_code=400, detail=f"Invalid role")
        assignment.role_in_country = body.role_in_country
    if body.is_active is not None:
        assignment.is_active = body.is_active
    if body.notes is not None:
        assignment.notes = body.notes

    assignment.updated_at = _utcnow()
    commit_and_refresh(db, assignment)
    return {"message": "Assignment updated", "assignment": _staff_payload(assignment)}


@router.delete("/countries/{code}/staff/{user_id}")
def remove_staff_from_country(
    code: str,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
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
    commit_only(db)
    return {"message": "Staff removed from country"}


@router.get("/staff/my-countries")
def get_my_assigned_countries(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
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


@router.get("/staff/all-assignments")
def list_all_staff_assignments(
    role: Optional[str] = Query(None),
    active_only: bool = Query(True),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
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

