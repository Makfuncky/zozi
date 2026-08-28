"""Employee logistics router — internal staff oversight of logistics partners.

Per ARCHITECTURE_DIAGRAM.md §3, this is a thin per-actor router:
auth context + require_feature(...) + one service call.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Path
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional

from infrastructure.database.database import get_db
from infrastructure.security.dependencies import require_employee
from rbac.dependencies import require_feature

router = APIRouter(prefix="/api/v1/employee/logistics", tags=["employee", "logistics"])

# Country code regex constraint (ISO 3166-1 alpha-2)
COUNTRY_CODE_PATH = Path(..., pattern=r"^[A-Z]{2}$", description="ISO 3166-1 alpha-2 country code")


# === Pydantic Schemas ===

class PartnerCreateRequest(BaseModel):
    name: str
    contact_email: str
    contact_phone: str
    country_code: str = Field(..., pattern=r"^[A-Z]{2}$")
    address: Optional[str] = None


class PartnerUpdateRequest(BaseModel):
    name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    is_active: Optional[bool] = None


# === Partner Management ===

@router.get("/{country_code}/partners")
def list_partners(
    country_code: str = COUNTRY_CODE_PATH,
    include_deleted: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    _: dict = Depends(require_employee),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("logistics.partners.manage")),
):
    from domains.logistics.services.core.admin_logistics_service import list_partners_paginated
    return list_partners_paginated(country_code=country_code, include_deleted=include_deleted, limit=page_size, cursor=None, db=db)


@router.post("/{country_code}/partners")
def create_partner(
    country_code: str = COUNTRY_CODE_PATH,
    data: PartnerCreateRequest = None,
    _: dict = Depends(require_employee),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("logistics.partners.manage")),
):
    from domains.logistics.services.partners.service import create_partner
    return create_partner(data, _, db)


@router.put("/{country_code}/partners/{partner_id}")
def update_partner(
    country_code: str = COUNTRY_CODE_PATH,
    partner_id: int = Path(...),
    data: PartnerUpdateRequest = None,
    _: dict = Depends(require_employee),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("logistics.partners.manage")),
):
    from domains.logistics.services.partners.service import update_partner
    return update_partner(partner_id, data, _, db)


@router.post("/{country_code}/partners/{partner_id}/approve")
def approve_partner(
    country_code: str = COUNTRY_CODE_PATH,
    partner_id: int = Path(...),
    _: dict = Depends(require_employee),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("logistics.partners.manage")),
):
    from domains.logistics.services.core.admin_logistics_service import approve_partner
    return approve_partner(db, partner_id, country_code)


@router.post("/{country_code}/partners/{partner_id}/reject")
def reject_partner(
    country_code: str = COUNTRY_CODE_PATH,
    partner_id: int = Path(...),
    _: dict = Depends(require_employee),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("logistics.partners.manage")),
):
    from domains.logistics.services.core.admin_logistics_service import reject_partner
    return reject_partner(db, partner_id, country_code)


@router.post("/{country_code}/partners/{partner_id}/toggle-active")
def toggle_partner_active(
    country_code: str = COUNTRY_CODE_PATH,
    partner_id: int = Path(...),
    _: dict = Depends(require_employee),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("logistics.partners.manage")),
):
    from domains.logistics.services.core.admin_logistics_service import toggle_partner_active
    return toggle_partner_active(db, partner_id, country_code)


# === Dashboard ===

@router.get("/{country_code}/dashboard")
def logistics_dashboard(
    country_code: str = COUNTRY_CODE_PATH,
    _: dict = Depends(require_employee),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("logistics.shipping.tracking")),
):
    from domains.logistics.services.core.admin_logistics_operations_service import get_logistics_overview
    return get_logistics_overview(db)
