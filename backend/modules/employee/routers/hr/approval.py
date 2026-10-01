"""Approval chain, country scope, localization, and authority threshold sub-router."""
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from infrastructure.security.dependencies import get_current_user
from infrastructure.database.database import get_db
from domains.hr.services.hr_employee_service import get_hr_employee_service
from domains.hr.services.authority_policy import get_required_authority
from domains.governance.ports import get_approval_chain
from rbac.dependencies import require_feature

router = APIRouter()


@router.post("/approval-chain")
def approval_chain(payload: dict, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("hr.create"))
):
    return {"approvers": get_approval_chain(db, employee_id=payload.get("employee_id", 0), resource_type=payload.get("resource_type", "leave"), min_authority_level=payload.get("min_authority_level"))}


@router.get("/country-scope/{user_id}")
def user_country_scope(user_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("hr.read"))
):
    return get_hr_employee_service(db).get_user_country_scope(db, user_id)


@router.post("/country-scope/switch")
def switch_country_scope(country_code: str = Query(..., min_length=2, max_length=10), db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("hr.create"))
):
    user_id = int(current_user.get("id", 0))
    normalized = country_code.upper()
    role = str(current_user.get("role", "")).lower()
    return get_hr_employee_service(db).switch_country_scope(db, user_id, normalized, role)


@router.get("/localization/{country_code}")
def country_localization(country_code: str = Path(..., min_length=2, max_length=10), db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("hr.read"))
):
    normalized = country_code.upper()
    return get_hr_employee_service(db).get_country_localization(db, normalized)


@router.get("/required-authority/{resource_type}")
def required_authority_for_resource(
    resource_type: str = Path(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("hr.read")),
):
    """Delegates to domains.hr.services.authority_policy (Law 2 — no business data here)."""
    level = get_required_authority(resource_type)
    if resource_type not in {
        "leave", "expense_500", "expense_2000", "expense_10000",
        "payroll_release", "offboarding_approve", "disciplinary_final",
        "hiring_approve",
    }:
        raise HTTPException(status_code=404, detail=f"Unknown resource_type: {resource_type}")
    return {
        "resource_type": resource_type,
        "required_authority_level": level,
    }