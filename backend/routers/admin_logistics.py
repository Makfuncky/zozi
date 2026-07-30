"""Admin logistics router."""
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from db.database import get_db
from models import LogisticsPartner, User
from db.schemas import ArchiveRequest, BulkActionRequest
from utils.dependencies import require_admin, require_super_admin
from utils.country_rls import get_country_or_404
from utils.rls_interceptor import set_rls_context, clear_rls_context
from controllers.admin_controller import archive_entity, restore_entity, bulk_archive_entities, bulk_restore_entities, hard_delete_entity

router = APIRouter()


@router.get("/{country_code}/partners")
def list_partners(country_code: str = Path(..., description="ISO country code"), include_deleted: bool = False, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), _: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        q = db.query(LogisticsPartner).filter(LogisticsPartner.country_code == country_code.upper())
        if not include_deleted: q = q.filter(LogisticsPartner.is_deleted == False)
        total = q.count()
        rows = q.offset((page - 1) * page_size).limit(page_size).all()
        return {"data": rows, "total": total, "page": page, "page_size": page_size}
    finally:
        clear_rls_context()


@router.put("/{country_code}/partners/{partner_id}/approve")
def approve_partner(country_code: str = Path(..., description="ISO country code"), partner_id: int = Path(...), _: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        p = db.query(LogisticsPartner).filter(LogisticsPartner.id == partner_id, LogisticsPartner.country_code == country_code.upper()).first()
        if not p: raise HTTPException(404)
        p.verification_status = "approved"
        db.commit()
        return {"message": "Partner approved"}
    finally:
        clear_rls_context()


@router.put("/{country_code}/partners/{partner_id}/reject")
def reject_partner(country_code: str = Path(..., description="ISO country code"), partner_id: int = Path(...), _: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        p = db.query(LogisticsPartner).filter(LogisticsPartner.id == partner_id, LogisticsPartner.country_code == country_code.upper()).first()
        if not p: raise HTTPException(404)
        p.verification_status = "rejected"
        db.commit()
        return {"message": "Partner rejected"}
    finally:
        clear_rls_context()


@router.post("/{country_code}/partners/{partner_id}/toggle-active")
def toggle_partner_active(country_code: str = Path(..., description="ISO country code"), partner_id: int = Path(...), _: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        p = db.query(LogisticsPartner).filter(LogisticsPartner.id == partner_id, LogisticsPartner.country_code == country_code.upper()).first()
        if not p: raise HTTPException(404)
        p.status = "suspended" if p.status == "active" else "active"
        db.commit()
        return {"message": f"Partner {'suspended' if p.status == 'suspended' else 'activated'}"}
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

