"""Org-units and reporting chain sub-router — thin delegators (Law 2)."""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from infrastructure.security.dependencies import get_current_user
from infrastructure.database.database import get_db
from domains.hr.services.hr_employee_service import get_hr_employee_service
from domains.hr.services.hierarchy.hierarchy_service import (
    get_org_chart as get_hierarchy_org_chart,
    get_org_unit_subtree,
    get_org_unit_path,
    get_employees_in_subtree,
    rebuild_paths,
    get_user_chain,
    get_all_subordinates,
    get_team_members,
    can_manage,
    reassign_manager,
    backfill_authority_levels,
)
from rbac.dependencies import require_feature

router = APIRouter()


@router.get("/org-units")
def list_org_units(country_code: Optional[str] = Query(None), db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("hr.read"))
):
    return get_hr_employee_service(db).list_org_units(db, country_code=country_code)


@router.post("/org-units", status_code=201)
def create_org_unit(payload: dict, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("hr.create"))
):
    return get_hr_employee_service(db).create_org_unit(db, payload)


@router.put("/org-units/{unit_id}")
def update_org_unit(unit_id: int, payload: dict = None, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("hr.update"))
):
    return get_hr_employee_service(db).update_org_unit(db, unit_id, payload or {})


@router.get("/org-chart/{org_unit_id}")
def org_chart_detail(org_unit_id: Optional[int] = None, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("hr.read"))
):
    return get_hierarchy_org_chart(db, org_unit_id)


@router.get("/org-units/{unit_id}/subtree")
def org_unit_subtree(unit_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("hr.read"))
):
    return {"subtree": get_org_unit_subtree(db, unit_id)}


@router.get("/org-units/{unit_id}/path")
def org_unit_ancestor_path(unit_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("hr.read"))
):
    return {"path": get_org_unit_path(db, unit_id)}


@router.get("/org-units/{unit_id}/employees")
def employees_in_subtree(unit_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("hr.read"))
):
    return {"employees": get_employees_in_subtree(db, unit_id)}


@router.post("/org-units/rebuild-paths")
def rebuild_org_unit_paths(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("hr.create"))
):
    updated = rebuild_paths(db)
    return {"message": f"Rebuilt paths for {updated} org units"}


@router.get("/employee/{user_id}/chain")
def employee_chain(user_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("hr.read"))
):
    return {"chain": get_user_chain(db, user_id)}


@router.get("/employee/{user_id}/subordinates")
def employee_subordinates(user_id: int, direct_only: bool = Query(False), db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("hr.read"))
):
    if direct_only:
        return {"subordinates": get_team_members(db, user_id)}
    return {"subordinates": get_all_subordinates(db, user_id)}


@router.get("/employee/{user_id}/can-manage/{target_user_id}")
def check_can_manage(user_id: int, target_user_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("hr.read"))
):
    return {"can_manage": can_manage(db, user_id, target_user_id)}


@router.post("/reassign-manager")
def reassign_employee_manager(payload: dict, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("hr.create"))
):
    return reassign_manager(db, payload.get("employee_user_id", 0), payload.get("new_manager_user_id", 0))


@router.post("/backfill-authority-levels")
def refresh_authority_levels(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("hr.create"))
):
    updated = backfill_authority_levels(db)
    return {"message": f"Updated {updated} employee authority levels"}