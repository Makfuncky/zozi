"""Admin logistics router."""
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from infrastructure.database.database import get_db
from domains.accounts.models.user import User
from infrastructure.database.schemas import ArchiveRequest, BulkActionRequest
from infrastructure.utils.dependencies import require_admin, require_super_admin
from domains.country.utils.country_rls import get_country_or_404
from infrastructure.utils.rls_interceptor import set_rls_context, clear_rls_context
from domains.governance.services.misc_service import archive_entity
from domains.governance.services.misc_service import restore_entity
from domains.catalog.services.bulk_ops_write_service import bulk_archive_entities
from domains.catalog.services.bulk_ops_write_service import bulk_restore_entities
from domains.governance.services.misc_service import hard_delete_entity
from domains.logistics.services.partner_geography_service import approve_partner
from domains.logistics.services.partner_geography_service import list_partners
from domains.logistics.services.partner_geography_service import reject_partner
from domains.logistics.services.partner_geography_service import toggle_partner_active

router = APIRouter(prefix="/api/v1/admin")


@router.get("/{country_code}/partners")
def list_partners_route(country_code: str = Path(..., description="ISO country code"), include_deleted: bool = False, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), _: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return list_partners(db, country_code, include_deleted, page, page_size)
    finally:
        clear_rls_context()


@router.put("/{country_code}/partners/{partner_id}/approve")
def approve_partner_route(country_code: str = Path(..., description="ISO country code"), partner_id: int = Path(...), _: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return approve_partner(db, partner_id, country_code)
    finally:
        clear_rls_context()


@router.put("/{country_code}/partners/{partner_id}/reject")
def reject_partner_route(country_code: str = Path(..., description="ISO country code"), partner_id: int = Path(...), _: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return reject_partner(db, partner_id, country_code)
    finally:
        clear_rls_context()


@router.post("/{country_code}/partners/{partner_id}/toggle-active")
def toggle_partner_active_route(country_code: str = Path(..., description="ISO country code"), partner_id: int = Path(...), _: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return toggle_partner_active(db, partner_id, country_code)
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
