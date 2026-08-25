"""Auto-migrated service logic from routers/hierarchy.py."""
from __future__ import annotations

import logging

from typing import Optional

from fastapi import Depends, HTTPException, Path, Query

from pydantic import BaseModel, Field

from sqlalchemy.orm import Session

from domains.accounts.services.auth.auth_service import get_current_user

from infrastructure.database.database import get_db

from domains.country.models.countries import CountryConfig
from domains.country.models.country_enhancements import CountryHolidayCalendar
from domains.country.models.country_enhancements import CountryStaffAssignment
from domains.hr.models.employee_models import OrgUnit

from domains.country.models.country_enhancements import CountryLocalization

# NOTE: The following imports were removed because they were self-imports
# (importing from domains.hr.hierarchy_service which is this same file).

class ManagerReassign(BaseModel):
    employee_user_id: int
    new_manager_user_id: int

class MatrixAssign(BaseModel):
    employee_id: int
    matrix_manager_id: int
    relation_type: str = "matrix_manager"
    notes: Optional[str] = None

class ApprovalChainQuery(BaseModel):
    employee_id: int
    resource_type: str = "leave"
    min_authority_level: Optional[int] = None

def _update_unit_path(db: Session, unit: OrgUnit) -> None:
    """Compute the materialized path and depth for a unit based on its parent."""
    if unit.parent_id:
        parent = db.query(OrgUnit).filter(OrgUnit.id == unit.parent_id).first()
        if parent:
            unit.path = f"{parent.path}{unit.id}/" if parent.path else f"/{parent.id}/{unit.id}/"
            unit.depth = (parent.depth or 0) + 1
        else:
            unit.path = f"/{unit.id}/"
            unit.depth = 0
    else:
        unit.path = f"/{unit.id}/"
        unit.depth = 0
    db.flush()

def list_org_units(country_code: Optional[str], db: Session, current_user: dict):
    q = db.query(OrgUnit).filter(OrgUnit.is_active == True)
    if country_code:
        q = q.filter(OrgUnit.country_code == country_code)
    units = q.order_by(OrgUnit.path, OrgUnit.name).all()
    return {
        "units": [
            {
                "id": u.id,
                "name": u.name,
                "parent_id": u.parent_id,
                "path": u.path,
                "depth": u.depth,
                "level": u.level,
                "country_code": u.country_code,
                "is_active": u.is_active,
            }
            for u in units
        ]
    }

def create_org_unit(payload: OrgUnitCreate, db: Session, current_user: dict):
    unit = OrgUnit(
        name=payload.name,
        parent_id=payload.parent_id,
        country_code=payload.country_code,
        level=payload.level,
    )
    db.add(unit)
    db.flush()
    _update_unit_path(db, unit)
    db.commit()
    db.refresh(unit)
    return {
        "id": unit.id,
        "name": unit.name,
        "path": unit.path,
        "depth": unit.depth,
    }

def update_org_unit(unit_id: int, payload: OrgUnitUpdate, db: Session, current_user: dict):
    unit = db.query(OrgUnit).filter(OrgUnit.id == unit_id).first()
    if not unit:
        raise HTTPException(status_code=404, detail="Org unit not found")

    if payload.name is not None:
        unit.name = payload.name
    if payload.level is not None:
        unit.level = payload.level
    if payload.is_active is not None:
        unit.is_active = payload.is_active
    if payload.parent_id is not None:
        unit.parent_id = payload.parent_id

    db.flush()
    _update_unit_path(db, unit)
    db.commit()
    return {"id": unit.id, "path": unit.path, "depth": unit.depth}

def org_chart(org_unit_id: Optional[int], db: Session, current_user: dict):
    return get_org_chart(db, org_unit_id)

def org_unit_subtree(unit_id: int, db: Session, current_user: dict):
    return {"subtree": get_org_unit_subtree(db, unit_id)}

def org_unit_ancestor_path(unit_id: int, db: Session, current_user: dict):
    return {"path": get_org_unit_path(db, unit_id)}

def employees_in_subtree(unit_id: int, db: Session, current_user: dict):
    return {"employees": get_employees_in_subtree(db, unit_id)}

def rebuild_org_unit_paths(db: Session, current_user: dict):
    updated = rebuild_paths(db)
    db.commit()
    return {"message": f"Rebuilt paths for {updated} org units"}

def employee_chain(user_id: int, db: Session, current_user: dict):
    return {"chain": get_user_chain(db, user_id)}

def employee_subordinates(user_id: int, direct_only: bool, db: Session, current_user: dict):
    if direct_only:
        return {"subordinates": get_team_members(db, user_id)}
    return {"subordinates": get_all_subordinates(db, user_id)}

def check_can_manage(user_id: int, target_user_id: int, db: Session, current_user: dict):
    return {"can_manage": can_manage(db, user_id, target_user_id)}

def reassign_employee_manager(payload: ManagerReassign, db: Session, current_user: dict):
    result = reassign_manager(db, payload.employee_user_id, payload.new_manager_user_id)
    db.commit()
    return result

def refresh_authority_levels(db: Session, current_user: dict):
    updated = backfill_authority_levels(db)
    db.commit()
    return {"message": f"Updated {updated} employee authority levels"}

def assign_matrix(payload: MatrixAssign, db: Session, current_user: dict):
    result = assign_matrix_manager(
        db,
        employee_id=payload.employee_id,
        matrix_manager_id=payload.matrix_manager_id,
        relation_type=payload.relation_type,
        notes=payload.notes,
    )
    db.commit()
    return result

def remove_matrix(relation_id: int, db: Session, current_user: dict):
    result = remove_matrix_manager(db, relation_id)
    db.commit()
    return result

def matrix_managers(employee_id: int, db: Session, current_user: dict):
    return {"matrix_managers": get_matrix_managers(db, employee_id)}

def matrix_subordinates(manager_id: int, db: Session, current_user: dict):
    return {"matrix_subordinates": get_matrix_subordinates(db, manager_id)}

def detect_circular(employee_id: int, proposed_manager_id: int, db: Session, current_user: dict):
    is_circular = detect_circular_reporting(db, employee_id, proposed_manager_id)
    return {
        "is_circular": is_circular,
        "message": "Circular reporting detected" if is_circular else "No circular relationship",
    }

def approval_chain(payload: ApprovalChainQuery, db: Session, current_user: dict):
    return {
        "approvers": get_approval_chain(
            db,
            employee_id=payload.employee_id,
            resource_type=payload.resource_type,
            min_authority_level=payload.min_authority_level,
        )
    }

def user_country_scope(user_id: int, db: Session, current_user: dict):
    """Get all country assignments for a user."""
    assignments = (
        db.query(CountryStaffAssignment)
        .filter(
            CountryStaffAssignment.user_id == user_id,
            CountryStaffAssignment.is_active == True,
        )
        .all()
    )
    return {
        "countries": [
            {
                "id": a.id,
                "country_code": a.country_code,
                "role_in_country": a.role_in_country,
            }
            for a in assignments
        ]
    }

def switch_country_scope(country_code: str, db: Session, current_user: dict):
    """Switch the active country scope for the current user (sets RLS context)."""
    user_id = int(current_user.get("id", 0))
    normalized = country_code.upper()

    # Verify the user has access to this country
    assignment = (
        db.query(CountryStaffAssignment)
        .filter(
            CountryStaffAssignment.user_id == user_id,
            CountryStaffAssignment.country_code == normalized,
            CountryStaffAssignment.is_active == True,
        )
        .first()
    )
    role = str(current_user.get("role", "")).lower()
    if not assignment and role not in ("admin", "super_admin"):
        raise HTTPException(status_code=403, detail=f"No access to country '{normalized}'")

    # Set RLS context
    from infrastructure.utils.rls_interceptor import set_rls_context
    set_rls_context(normalized)

    return {"active_country": normalized, "message": f"Switched to {normalized}"}

def country_localization(country_code: str, db: Session, current_user: dict):
    """Get localization settings for a country (leave policies, holidays, labor rules)."""
    normalized = country_code.upper()
    country = db.query(CountryConfig).filter(CountryConfig.code == normalized).first()
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")

    holidays = (
        db.query(CountryHolidayCalendar)
        .filter(CountryHolidayCalendar.country_code == normalized)
        .order_by(CountryHolidayCalendar.date)
        .all()
    )
    localization = (
        db.query(CountryLocalization)
        .filter(CountryLocalization.country_code == normalized)
        .all()
    )

    return {
        "country": {
            "code": country.code,
            "name": country.name,
            "currency": country.currency,
            "timezone": country.timezone,
            "language": country.language,
        },
        "holidays": [
            {
                "id": h.id,
                "name": h.holiday_name,
                "date": str(h.date),
                "type": h.holiday_type,
            }
            for h in holidays
        ],
        "localization": {
            loc.key: loc.value
            for loc in localization
        },
    }

def required_authority_for_resource(resource_type: str, db: Session, current_user: dict):
    thresholds = {
        "leave": 1,
        "expense_500": 2,
        "expense_2000": 3,
        "expense_10000": 4,
        "payroll_release": 4,
        "offboarding_approve": 3,
        "disciplinary_final": 4,
        "hiring_approve": 3,
    }
    return {
        "resource_type": resource_type,
        "required_authority_level": thresholds.get(resource_type, 1),
    }


# ──────────────────────────────────────────────
# Stub implementations for missing functions
# These functions were referenced but never implemented.
# TODO: Implement these functions properly.
# ──────────────────────────────────────────────

def get_all_subordinates(user_id: int, db: Session, direct_only: bool = False) -> list:
    """Get all subordinates of a user. STUB - needs implementation."""
    raise NotImplementedError("get_all_subordinates is not implemented")


def can_manage(manager_id: int, target_user_id: int, db: Session) -> bool:
    """Check if a manager can manage a target user. STUB - needs implementation."""
    raise NotImplementedError("can_manage is not implemented")


def backfill_authority_levels(db: Session) -> None:
    """Backfill authority levels. STUB - needs implementation."""
    raise NotImplementedError("backfill_authority_levels is not implemented")


def get_authority_level(user_id: int, db: Session) -> int:
    """Get the authority level of a user. STUB - needs implementation."""
    raise NotImplementedError("get_authority_level is not implemented")


def get_home_org_unit(user_id: int, db: Session) -> Optional[dict]:
    """Get the home org unit of a user. STUB - needs implementation."""
    raise NotImplementedError("get_home_org_unit is not implemented")


def get_org_chart(org_unit_id: Optional[int], db: Session, current_user: dict) -> dict:
    """Get the org chart. STUB - needs implementation."""
    raise NotImplementedError("get_org_chart is not implemented")


def get_team_members(user_id: int, db: Session, direct_only: bool = False) -> list:
    """Get team members. STUB - needs implementation."""
    raise NotImplementedError("get_team_members is not implemented")


def get_user_chain(user_id: int, db: Session) -> list:
    """Get the user chain. STUB - needs implementation."""
    raise NotImplementedError("get_user_chain is not implemented")


def is_in_chain(manager_id: int, target_user_id: int, db: Session) -> bool:
    """Check if a user is in the chain of another. STUB - needs implementation."""
    raise NotImplementedError("is_in_chain is not implemented")


def reassign_manager(payload: dict, db: Session, current_user: dict) -> dict:
    """Reassign a manager. STUB - needs implementation."""
    raise NotImplementedError("reassign_manager is not implemented")


