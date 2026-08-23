"""Service methods for country staff data access.

Each top-level function owns its database session via ``get_db_context`` so the
router layer never injects or touches a SQLAlchemy session directly.
"""
from __future__ import annotations
from typing import List
from typing import Any, Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from domains.country.models.country_enhancements import CountryStaffAssignment
from infrastructure.utils.pagination import SAFE_QUERY_LIMIT
import structlog
logger = structlog.get_logger(__name__)


def get_country_staff_by_country(db: Session, country_code: str) -> list[CountryStaffAssignment]:
    """Get all staff assignments for a country."""
    return db.query(CountryStaffAssignment).filter(
        CountryStaffAssignment.country_code == country_code
    ).limit(SAFE_QUERY_LIMIT).all()


def _staff_payload(row: CountryStaffAssignment, user_map: dict[int, Any]) -> dict[str, Any]:
    user = user_map.get(row.user_id)
    return {
        "id": row.id,
        "user_id": row.user_id,
        "country_code": row.country_code,
        "role_in_country": row.role_in_country,
        "user_name": getattr(user, "username", "") if user else "",
        "user_email": getattr(user, "email", "") if user else "",
        "is_active": row.is_active,
        "assigned_by": row.assigned_by,
        "notes": row.notes,
        "created_at": row.created_at,
    }


def _user_map(db: Session, rows: list[CountryStaffAssignment]) -> dict[int, Any]:
    from domains.governance.models.user import User
    user_ids = [r.user_id for r in rows]
    if not user_ids:
        return {}
    return {u.id: u for u in db.query(User).filter(User.id.in_(user_ids)).limit(SAFE_QUERY_LIMIT).all()}


def list_country_staff(
    country_code: str,
    active_only: bool = True,
    limit: int = 20,
    cursor: Optional[str] = None,
) -> dict:
    """List staff assignments for a country (cursor-paginated)."""
    from typing import Optional
    from infrastructure.database.database import get_db_context
    from infrastructure.utils.pagination import cursor_paginate_asc, build_cursor_pagination_payload

    with get_db_context() as db:
        q = db.query(CountryStaffAssignment).filter(
            CountryStaffAssignment.country_code == country_code.upper()
        )
        if active_only:
            q = q.filter(CountryStaffAssignment.is_active == True)
        q = q.order_by(CountryStaffAssignment.id.asc())
        result = cursor_paginate_asc(q, cursor=cursor, page_size=limit)
        user_map = _user_map(db, result.items)
        return build_cursor_pagination_payload(
            [_staff_payload(r, user_map) for r in result.items],
            result.next_cursor,
            result.page_size,
        )


def assign_staff_to_country(
    country_code: str,
    body: Any,
    current_user: dict,
) -> dict[str, Any]:
    """Assign a user to a country with a role."""
    from fastapi import HTTPException
    from infrastructure.database.database import get_db_context
    from domains.governance.models.user import User
    user_id = int(getattr(body, "user_id", 0))
    role_in_country = getattr(body, "role_in_country", "country_manager") or "country_manager"
    notes = getattr(body, "notes", None)
    with get_db_context() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        existing = db.query(CountryStaffAssignment).filter(
            CountryStaffAssignment.user_id == user_id,
            CountryStaffAssignment.country_code == country_code.upper(),
        ).first()
        if existing:
            raise HTTPException(status_code=409, detail="Staff already assigned to this country")
        assignment = CountryStaffAssignment(
            user_id=user_id,
            country_code=country_code.upper(),
            role_in_country=role_in_country,
            notes=notes,
            assigned_by=current_user.get("id"),
        )
        db.add(assignment)
        db.commit()
        db.refresh(assignment)
        return {"id": assignment.id, "user_id": user_id, "country_code": country_code.upper(), "role_in_country": role_in_country}


def update_staff_assignment(
    country_code: str,
    assignment_id: int,
    body: Any,
) -> dict[str, Any]:
    """Update a staff assignment (role, active, notes)."""
    from fastapi import HTTPException
    from infrastructure.database.database import get_db_context
    with get_db_context() as db:
        row = db.query(CountryStaffAssignment).filter(
            CountryStaffAssignment.id == assignment_id,
            CountryStaffAssignment.country_code == country_code.upper(),
        ).first()
        if not row:
            raise HTTPException(status_code=404, detail="Assignment not found")
        payload = body.model_dump(exclude_unset=True) if hasattr(body, "model_dump") else vars(body)
        for key, value in payload.items():
            if hasattr(row, key) and value is not None:
                setattr(row, key, value)
        db.commit()
        db.refresh(row)
        user_map = _user_map(db, [row])
        return _staff_payload(row, user_map)


def remove_staff_from_country(country_code: str, user_id: int) -> dict[str, Any]:
    """Soft-delete (deactivate) a staff assignment for a user in a country."""
    from fastapi import HTTPException
    from infrastructure.database.database import get_db_context
    with get_db_context() as db:
        row = db.query(CountryStaffAssignment).filter(
            CountryStaffAssignment.user_id == user_id,
            CountryStaffAssignment.country_code == country_code.upper(),
        ).first()
        if not row:
            raise HTTPException(status_code=404, detail="Assignment not found")
        row.is_active = False
        db.commit()
        return {"message": "Staff unassigned"}


def get_my_assigned_countries(
    user_id: int,
    limit: int = 20,
    cursor: Optional[str] = None,
) -> dict:
    """Get countries where the given user is an active staff member (cursor-paginated)."""
    from typing import Optional
    from infrastructure.database.database import get_db_context
    from infrastructure.utils.pagination import cursor_paginate_asc, build_cursor_pagination_payload

    with get_db_context() as db:
        query = (
            db.query(CountryStaffAssignment)
            .filter(
                CountryStaffAssignment.user_id == user_id,
                CountryStaffAssignment.is_active == True,
            )
            .order_by(CountryStaffAssignment.id.asc())
        )
        result = cursor_paginate_asc(query, cursor=cursor, page_size=limit)
        return build_cursor_pagination_payload(
            [_staff_payload(r, {}) for r in result.items],
            result.next_cursor,
            result.page_size,
        )


def list_all_staff_assignments(
    role: Optional[str] = None,
    active_only: bool = True,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """List all staff assignments across countries, optionally filtered by role."""
    from infrastructure.database.database import get_db_context
    with get_db_context() as db:
        q = db.query(CountryStaffAssignment)
        if role:
            q = q.filter(CountryStaffAssignment.role_in_country == role)
        if active_only:
            q = q.filter(CountryStaffAssignment.is_active == True)
        rows = q.order_by(CountryStaffAssignment.created_at.desc()).limit(limit).all()
        user_map = _user_map(db, rows)
        return [_staff_payload(r, user_map) for r in rows]

# === Merged from accounts/services/country_staff_service.py ===

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



