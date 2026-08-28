from __future__ import annotations

"""Admin logistics router — canonical."""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from sqlalchemy.orm import Session
from typing import Optional

from infrastructure.database.database import get_db
from infrastructure.security.dependencies import require_admin, require_super_admin
from rbac.dependencies import require_feature
from domains.country.utils.country_rls import get_country_or_404
from infrastructure.database.rls_interceptor import set_rls_context, clear_rls_context
from domains.logistics.services.core.admin_logistics_service import approve_partner
from domains.logistics.services.core.admin_logistics_service import hard_delete_partner
from domains.logistics.services.core.admin_logistics_service import list_partners_paginated
from domains.logistics.services.core.admin_logistics_service import reject_partner
from domains.logistics.services.core.admin_logistics_service import toggle_partner_active

router = APIRouter(prefix="/api/v1/admin/logistics", tags=["admin", "logistics"])


@router.get("/admin_logistics_routes/health")
def health(_: dict = Depends(require_admin),
    _rf_gate: None = Depends(require_feature("logistics.shipping.tracking"))
):
    return {"status": "ok", "router": "admin_logistics_routes", "prefix": "/api/v1/admin"}


@router.get("/{country_code}/partners")
def list_partners_route(
    country_code: str = Path(..., description="ISO country code"),
    include_deleted: bool = False,
    limit: int = Query(50, ge=1, le=100),
    cursor: str | None = Query(None, description="Cursor for keyset pagination"),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("logistics.partners.manage")),
):
    return list_partners_paginated(country_code, include_deleted, limit, cursor, db)


@router.put("/{country_code}/partners/{partner_id}/approve")
def approve_partner_route(
    country_code: str = Path(..., description="ISO country code"),
    partner_id: int = Path(...),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("logistics.partners.manage")),
):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return approve_partner(db, partner_id, country_code)
    finally:
        clear_rls_context()


@router.put("/{country_code}/partners/{partner_id}/reject")
def reject_partner_route(
    country_code: str = Path(..., description="ISO country code"),
    partner_id: int = Path(...),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("logistics.partners.manage")),
):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return reject_partner(db, partner_id, country_code)
    finally:
        clear_rls_context()


@router.post("/{country_code}/partners/{partner_id}/toggle-active")
def toggle_partner_active_route(
    country_code: str = Path(..., description="ISO country code"),
    partner_id: int = Path(...),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("logistics.partners.manage")),
):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return toggle_partner_active(db, partner_id, country_code)
    finally:
        clear_rls_context()


@router.post("/{country_code}/partners/{partner_id}/archive")
def archive_partner(
    country_code: str = Path(..., description="ISO country code"),
    partner_id: int = Path(...),
    payload: Optional[dict] = Body(None),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("logistics.partners.manage")),
):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        from domains.logistics.services.core.admin_logistics_service import archive_partner as svc_archive_partner
        reason = payload.get("reason") if payload else None
        return svc_archive_partner(db, partner_id, country_code, reason)
    finally:
        clear_rls_context()


@router.post("/{country_code}/partners/{partner_id}/restore")
def restore_partner(
    country_code: str = Path(..., description="ISO country code"),
    partner_id: int = Path(...),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("logistics.partners.manage")),
):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        from domains.logistics.services.core.admin_logistics_service import restore_partner as svc_restore_partner
        return svc_restore_partner(db, partner_id, country_code)
    finally:
        clear_rls_context()


@router.delete("/{country_code}/partners/{partner_id}")
def delete_partner_permanent(
    country_code: str = Path(..., description="ISO country code"),
    partner_id: int = Path(...),
    _: dict = Depends(require_super_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("logistics.partners.manage")),
):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return hard_delete_partner(db, partner_id, country_code)
    finally:
        clear_rls_context()
