"""Hierarchy Router — Org chart, reporting lines, matrix management, approval chains."""
from __future__ import annotations

import logging
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from controllers.auth_controller import get_current_user
from db.database import get_db
from models import Employee, OrgUnit, EmployeeRelation, EmployeeRole
from services.hierarchy_service import (
    get_org_chart,
    get_org_unit_subtree,
    get_org_unit_path,
    get_employees_in_subtree,
    get_user_chain,
    get_all_subordinates,
    get_team_members,
    can_manage,
    is_in_chain,
    reassign_manager,
    backfill_authority_levels,
    rebuild_paths,
    assign_matrix_manager,
    remove_matrix_manager,
    get_matrix_managers,
    get_matrix_subordinates,
    detect_circular_reporting,
    get_approval_chain,
)
from utils.country_rls import enforce_country_access, get_country_scope_from_db
from models import CountryStaffAssignment, CountryConfig, CountryHolidayCalendar
from models.country_enhancements import CountryLocalization

logger = logging.getLogger(__name__)

router = APIRouter()


# ══════════════════════════════════════════════════════════════════
#  Pydantic Schemas
# ══════════════════════════════════════════════════════════════════


class OrgUnitCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    parent_id: Optional[int] = None
    country_code: str
    level: int = 1


class OrgUnitUpdate(BaseModel):
    name: Optional[str] = None
    parent_id: Optional[int] = None
    is_active: Optional[bool] = None
    level: Optional[int] = None


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


# ══════════════════════════════════════════════════════════════════
#  Org Unit CRUD + Path Management
# ══════════════════════════════════════════════════════════════════


@router.get("/org-units", response_model=dict)
def list_org_units(
    country_code: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
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


@router.post("/org-units", status_code=201)
def create_org_unit(
    payload: OrgUnitCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
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


@router.put("/org-units/{unit_id}")
def update_org_unit(
    unit_id: int = Path(...),
    payload: OrgUnitUpdate = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
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


@router.get("/org-chart")
def org_chart(
    org_unit_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return get_org_chart(db, org_unit_id)


@router.get("/org-units/{unit_id}/subtree")
def org_unit_subtree(
    unit_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return {"subtree": get_org_unit_subtree(db, unit_id)}


@router.get("/org-units/{unit_id}/path")
def org_unit_ancestor_path(
    unit_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return {"path": get_org_unit_path(db, unit_id)}


@router.get("/org-units/{unit_id}/employees")
def employees_in_subtree(
    unit_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return {"employees": get_employees_in_subtree(db, unit_id)}


@router.post("/org-units/rebuild-paths")
def rebuild_org_unit_paths(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    updated = rebuild_paths(db)
    db.commit()
    return {"message": f"Rebuilt paths for {updated} org units"}


# ══════════════════════════════════════════════════════════════════
#  Employee Hierarchy & Reporting
# ══════════════════════════════════════════════════════════════════


@router.get("/employee/{user_id}/chain")
def employee_chain(
    user_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return {"chain": get_user_chain(db, user_id)}


@router.get("/employee/{user_id}/subordinates")
def employee_subordinates(
    user_id: int = Path(...),
    direct_only: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if direct_only:
        return {"subordinates": get_team_members(db, user_id)}
    return {"subordinates": get_all_subordinates(db, user_id)}


@router.get("/employee/{user_id}/can-manage/{target_user_id}")
def check_can_manage(
    user_id: int = Path(...),
    target_user_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return {"can_manage": can_manage(db, user_id, target_user_id)}


@router.post("/reassign-manager")
def reassign_employee_manager(
    payload: ManagerReassign,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = reassign_manager(db, payload.employee_user_id, payload.new_manager_user_id)
    db.commit()
    return result


@router.post("/backfill-authority-levels")
def refresh_authority_levels(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    updated = backfill_authority_levels(db)
    db.commit()
    return {"message": f"Updated {updated} employee authority levels"}


# ══════════════════════════════════════════════════════════════════
#  Matrix / Dotted-Line Management
# ══════════════════════════════════════════════════════════════════


@router.post("/matrix/assign")
def assign_matrix(
    payload: MatrixAssign,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = assign_matrix_manager(
        db,
        employee_id=payload.employee_id,
        matrix_manager_id=payload.matrix_manager_id,
        relation_type=payload.relation_type,
        notes=payload.notes,
    )
    db.commit()
    return result


@router.delete("/matrix/{relation_id}")
def remove_matrix(
    relation_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = remove_matrix_manager(db, relation_id)
    db.commit()
    return result


@router.get("/employee/{employee_id}/matrix-managers")
def matrix_managers(
    employee_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return {"matrix_managers": get_matrix_managers(db, employee_id)}


@router.get("/employee/{manager_id}/matrix-subordinates")
def matrix_subordinates(
    manager_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return {"matrix_subordinates": get_matrix_subordinates(db, manager_id)}


# ══════════════════════════════════════════════════════════════════
#  Circular Reference Detection & Approval Chains
# ══════════════════════════════════════════════════════════════════


@router.get("/detect-circular")
def detect_circular(
    employee_id: int = Query(...),
    proposed_manager_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    is_circular = detect_circular_reporting(db, employee_id, proposed_manager_id)
    return {
        "is_circular": is_circular,
        "message": "Circular reporting detected" if is_circular else "No circular relationship",
    }


@router.post("/approval-chain")
def approval_chain(
    payload: ApprovalChainQuery,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return {
        "approvers": get_approval_chain(
            db,
            employee_id=payload.employee_id,
            resource_type=payload.resource_type,
            min_authority_level=payload.min_authority_level,
        )
    }


# ══════════════════════════════════════════════════════════════════
#  Country Scope & Localization
# ══════════════════════════════════════════════════════════════════


@router.get("/country-scope/{user_id}")
def user_country_scope(
    user_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
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


@router.post("/country-scope/switch")
def switch_country_scope(
    country_code: str = Query(..., min_length=2, max_length=10),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
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
    from utils.rls_interceptor import set_rls_context
    set_rls_context(normalized)

    return {"active_country": normalized, "message": f"Switched to {normalized}"}


@router.get("/localization/{country_code}")
def country_localization(
    country_code: str = Path(..., min_length=2, max_length=10),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
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


# ══════════════════════════════════════════════════════════════════
#  Authority Level Helpers
# ══════════════════════════════════════════════════════════════════


@router.get("/required-authority/{resource_type}")
def required_authority_for_resource(
    resource_type: str = Path(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
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


# ══════════════════════════════════════════════════════════════════
#  Internal Helpers
# ══════════════════════════════════════════════════════════════════


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
