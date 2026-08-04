"""Admin logistics router."""
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from data.db import get_db
from data.schemas import CursorPage
from data.models import User
from data.schemas import ArchiveRequest, BulkActionRequest
from utils.dependencies import require_admin, require_super_admin
from utils.pagination import cursor_paginate_desc
from utils.country_rls import get_country_or_404
from utils.rls_interceptor import set_rls_context, clear_rls_context
from services.core.admin_operations_service import (
    archive_entity,
    restore_entity,
    bulk_archive_entities,
    bulk_restore_entities,
    hard_delete_entity,
)
from services.logistics.logistics_partner_write_service import (
    update_logistics_partner,
    get_partner_by_id,
    build_partners_query,
)

router = APIRouter()


@router.get("/{country_code}/partners", response_model=CursorPage)
def list_partners_route(
    country_code: str = Path(..., description="ISO country code"),
    include_deleted: bool = False,
    cursor: str | None = Query(None, description="Cursor for next page"),
    limit: int = Query(20, ge=1, le=100),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        q = build_partners_query(db, country_code.upper(), include_deleted)
        return cursor_paginate_desc(q, cursor=cursor, page_size=limit)
    finally:
        clear_rls_context()


@router.put("/{country_code}/partners/{partner_id}/approve")
def approve_partner(country_code: str = Path(..., description="ISO country code"), partner_id: int = Path(...), _: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        p = get_partner_by_id(db, partner_id, country_code.upper())
        if not p:
            raise HTTPException(404)
        update_logistics_partner(db, p, {"verification_status": "approved"})
        return {"message": "Partner approved"}
    finally:
        clear_rls_context()


@router.put("/{country_code}/partners/{partner_id}/reject")
def reject_partner(country_code: str = Path(..., description="ISO country code"), partner_id: int = Path(...), _: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        p = get_partner_by_id(db, partner_id, country_code.upper())
        if not p:
            raise HTTPException(404)
        update_logistics_partner(db, p, {"verification_status": "rejected"})
        return {"message": "Partner rejected"}
    finally:
        clear_rls_context()


@router.post("/{country_code}/partners/{partner_id}/toggle-active")
def toggle_partner_active(country_code: str = Path(..., description="ISO country code"), partner_id: int = Path(...), _: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        p = get_partner_by_id(db, partner_id, country_code.upper())
        if not p:
            raise HTTPException(404)
        new_status = "suspended" if p.status == "active" else "active"
        update_logistics_partner(db, p, {"status": new_status})
        return {"message": "Partner " + str(new_status)}
    finally:
        clear_rls_context()


@router.post("/{country_code}/partners/{partner_id}/archive")
def archive_partner(country_code: str = Path(..., description="ISO country code"), partner_id: int = Path(...), payload: ArchiveRequest = None, _: User = Depends(require_admin), db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return archive_entity("logistics_partner", partner_id, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db, payload.reason if payload else None)
    finally:
        clear_rls_context()


@router.post("/{country_code}/partners/{partner_id}/restore")
def restore_partner(country_code: str = Path(..., description="ISO country code"), partner_id: int = Path(...), _: User = Depends(require_admin), db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return restore_entity("logistics_partner", partner_id, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db)
    finally:
        clear_rls_context()


@router.post("/{country_code}/partners/bulk/archive")
def bulk_archive_partners(country_code: str = Path(..., description="ISO country code"), payload: BulkActionRequest = None, _: User = Depends(require_admin), db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return bulk_archive_entities("logistics_partner", payload.ids, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db, payload.reason)
    finally:
        clear_rls_context()


@router.post("/{country_code}/partners/bulk/restore")
def bulk_restore_partners(country_code: str = Path(..., description="ISO country code"), payload: BulkActionRequest = None, _: User = Depends(require_admin), db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return bulk_restore_entities("logistics_partner", payload.ids, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db)
    finally:
        clear_rls_context()


@router.delete("/{country_code}/partners/{partner_id}")
def delete_partner_permanent(country_code: str = Path(..., description="ISO country code"), partner_id: int = Path(...), _: User = Depends(require_super_admin), db: Session = Depends(get_db), current_user: User = Depends(require_super_admin)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return hard_delete_entity("logistics_partner", partner_id, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db)
    finally:
        clear_rls_context()
