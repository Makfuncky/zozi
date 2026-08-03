"""Admin users router."""
from fastapi import APIRouter, Depends, HTTPException, Query, Body, Path
from sqlalchemy.orm import Session
from data.db import get_db
from data.models import User
from data.schemas import UserOut, UserAdminUpdate, ArchiveRequest, BulkActionRequest
from utils.dependencies import require_admin
from utils.country_rls import get_country_or_404
from utils.rls_interceptor import set_rls_context, clear_rls_context
from utils.pagination import paginated_response
from services.core.admin_operations_service import archive_entity, restore_entity, bulk_archive_entities, bulk_restore_entities, hard_delete_entity, update_user_role, toggle_user_active, force_reset_password_admin, delete_user_admin

from services.write_helpers import commit_only, refresh_only
router = APIRouter()


@router.get("/users/{country_code}")
def list_users(country_code: str = Path(..., description="ISO country code"), page: int = Query(1, ge=1), size: int = Query(50), role: str = None, search: str = None, include_deleted: bool = False, _=Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        q = db.query(User).filter(User.country_code == country_code.upper())
        if role: q = q.filter(User.role == role)
        if search: q = q.filter(User.email.ilike(f"%{search}%") | User.full_name.ilike(f"%{search}%"))
        if not include_deleted: q = q.filter(User.is_deleted == False)
        return paginated_response(q, page, size)
    finally:
        clear_rls_context()


@router.put("/users/{country_code}/{user_id}", response_model=UserOut)
def update_user(country_code: str = Path(..., description="ISO country code"), user_id: int = Path(...), payload: UserAdminUpdate = None, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        u = db.query(User).filter(User.id == user_id, User.country_code == country_code.upper()).first()
        if not u: raise HTTPException(404)
        for k, v in payload.model_dump(exclude_unset=True).items(): setattr(u, k, v)
        commit_only(db); refresh_only(db, u)
        return u
    finally:
        clear_rls_context()


@router.post("/users/{country_code}/{user_id}/archive")
def archive_user(country_code: str = Path(..., description="ISO country code"), user_id: int = Path(...), payload: ArchiveRequest = None, _: User = Depends(require_admin), db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return archive_entity("user", user_id, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db, payload.reason if payload else None)
    finally:
        clear_rls_context()


@router.post("/users/{country_code}/{user_id}/restore")
def restore_user(country_code: str = Path(..., description="ISO country code"), user_id: int = Path(...), _: User = Depends(require_admin), db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return restore_entity("user", user_id, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db)
    finally:
        clear_rls_context()


@router.post("/users/{country_code}/{user_id}/toggle-active")
def toggle_user_active_route(country_code: str = Path(..., description="ISO country code"), user_id: int = Path(...), _: User = Depends(require_admin), db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return toggle_user_active(user_id, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db)
    finally:
        clear_rls_context()


@router.post("/users/{country_code}/{user_id}/reset-password")
def reset_user_password(country_code: str = Path(..., description="ISO country code"), user_id: int = Path(...), new_password: str = Body(..., min_length=6), _: User = Depends(require_admin), db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return force_reset_password_admin(user_id, new_password, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db)
    finally:
        clear_rls_context()


@router.post("/users/{country_code}/bulk/archive")
def bulk_archive_users(country_code: str = Path(..., description="ISO country code"), payload: BulkActionRequest = None, _: User = Depends(require_admin), db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return bulk_archive_entities("user", payload.ids, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db, payload.reason)
    finally:
        clear_rls_context()


@router.post("/users/{country_code}/bulk/restore")
def bulk_restore_users(country_code: str = Path(..., description="ISO country code"), payload: BulkActionRequest = None, _: User = Depends(require_admin), db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return bulk_restore_entities("user", payload.ids, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db)
    finally:
        clear_rls_context()


@router.post("/users/{country_code}/bulk-role")
def bulk_update_user_role(country_code: str = Path(..., description="ISO country code"), payload: dict = Body(...), _: User = Depends(require_admin), db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        user_ids = payload.get("user_ids", [])
        role = payload.get("role")
        if not user_ids or not role:
            raise HTTPException(400, "user_ids and role are required")
        updated = 0
        for uid in user_ids:
            try:
                update_user_role(uid, role, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db)
                updated += 1
            except HTTPException:
                pass
        return {"message": f"Updated {updated} users", "updated": updated}
    finally:
        clear_rls_context()


@router.post("/users/{country_code}/bulk-toggle-active")
def bulk_toggle_user_active(country_code: str = Path(..., description="ISO country code"), payload: dict = Body(...), _: User = Depends(require_admin), db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        user_ids = payload.get("user_ids", [])
        is_active = payload.get("is_active", True)
        if not user_ids:
            raise HTTPException(400, "user_ids is required")
        updated = 0
        for uid in user_ids:
            u = db.query(User).filter(User.id == uid, User.country_code == country_code.upper()).first()
            if u:
                u.is_active = is_active
                updated += 1
        commit_only(db)
        return {"message": f"Updated {updated} users", "updated": updated}
    finally:
        clear_rls_context()


@router.delete("/users/{country_code}/bulk")
def bulk_delete_users(country_code: str = Path(..., description="ISO country code"), payload: dict = Body(...), _: User = Depends(require_admin), db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        user_ids = payload.get("user_ids", [])
        if not user_ids:
            raise HTTPException(400, "user_ids is required")
        deleted = 0
        skipped = []
        for uid in user_ids:
            try:
                hard_delete_entity("user", uid, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db)
                deleted += 1
            except HTTPException as e:
                skipped.append({"id": uid, "reason": str(e.detail)})
        return {"deleted": deleted, "skipped": len(skipped), "skipped_details": skipped}
    finally:
        clear_rls_context()

@router.delete("/users/{country_code}/{user_id}")
def delete_user_permanent(country_code: str = Path(..., description="ISO country code"), user_id: int = Path(...), delete_orders: bool = Query(False), _: User = Depends(require_admin), db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return delete_user_admin(user_id, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db, delete_orders=delete_orders)
    finally:
        clear_rls_context()

