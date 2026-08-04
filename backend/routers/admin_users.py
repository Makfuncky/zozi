"""Admin users router."""
from fastapi import APIRouter, Depends, HTTPException, Path, Query, Body
from sqlalchemy.orm import Session
from data.db import get_db
from data.models import User
from data.schemas import UserOut, UserAdminUpdate, ArchiveRequest, BulkActionRequest
from utils.dependencies import require_admin
from utils.country_rls import get_country_or_404
from services.core.admin_operations_service import (
    archive_entity, restore_entity, bulk_archive_entities, bulk_restore_entities,
    hard_delete_entity, update_user_role, toggle_user_active, force_reset_password_admin, delete_user_admin
)
from services.core.admin_router_service import (
    list_users_by_country, update_user_in_db, bulk_toggle_users_active_in_db
)

router = APIRouter()


@router.get("/users/{country_code}")
def list_users(country_code: str = Path(..., description="ISO country code"), page: int = Query(1, ge=1), size: int = Query(50), role: str = None, search: str = None, include_deleted: bool = False, _=Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    return list_users_by_country(db, country_code, page=page, size=size, role=role, search=search, include_deleted=include_deleted)


@router.put("/users/{country_code}/{user_id}", response_model=UserOut)
def update_user(country_code: str = Path(..., description="ISO country code"), user_id: int = Path(...), payload: UserAdminUpdate = None, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    return update_user_in_db(db, country_code, user_id, payload.model_dump(exclude_unset=True))


@router.post("/users/{country_code}/{user_id}/archive")
def archive_user(country_code: str = Path(..., description="ISO country code"), user_id: int = Path(...), payload: ArchiveRequest = None, _: User = Depends(require_admin), db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    get_country_or_404(country_code.upper(), db)
    return archive_entity("user", user_id, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db, payload.reason if payload else None)


@router.post("/users/{country_code}/{user_id}/restore")
def restore_user(country_code: str = Path(..., description="ISO country code"), user_id: int = Path(...), _: User = Depends(require_admin), db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    get_country_or_404(country_code.upper(), db)
    return restore_entity("user", user_id, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db)


@router.post("/users/{country_code}/{user_id}/toggle-active")
def toggle_user_active_route(country_code: str = Path(..., description="ISO country code"), user_id: int = Path(...), _: User = Depends(require_admin), db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    get_country_or_404(country_code.upper(), db)
    return toggle_user_active(user_id, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db)


@router.post("/users/{country_code}/{user_id}/reset-password")
def reset_user_password(country_code: str = Path(..., description="ISO country code"), user_id: int = Path(...), new_password: str = Body(..., min_length=6), _: User = Depends(require_admin), db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    get_country_or_404(country_code.upper(), db)
    return force_reset_password_admin(user_id, new_password, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db)


@router.post("/users/{country_code}/bulk/archive")
def bulk_archive_users(country_code: str = Path(..., description="ISO country code"), payload: BulkActionRequest = None, _: User = Depends(require_admin), db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    get_country_or_404(country_code.upper(), db)
    return bulk_archive_entities("user", payload.ids, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db, payload.reason)


@router.post("/users/{country_code}/bulk/restore")
def bulk_restore_users(country_code: str = Path(..., description="ISO country code"), payload: BulkActionRequest = None, _: User = Depends(require_admin), db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    get_country_or_404(country_code.upper(), db)
    return bulk_restore_entities("user", payload.ids, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db)


@router.post("/users/{country_code}/bulk-role")
def bulk_update_user_role_route(country_code: str = Path(..., description="ISO country code"), payload: dict = Body(...), _: User = Depends(require_admin), db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    get_country_or_404(country_code.upper(), db)
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
    return {"message": "Updated " + str(updated) + " users", "updated": updated}


@router.post("/users/{country_code}/bulk-toggle-active")
def bulk_toggle_user_active_route(country_code: str = Path(..., description="ISO country code"), payload: dict = Body(...), _: User = Depends(require_admin), db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    get_country_or_404(country_code.upper(), db)
    user_ids = payload.get("user_ids", [])
    is_active = payload.get("is_active", True)
    if not user_ids:
        raise HTTPException(400, "user_ids is required")
    return bulk_toggle_users_active_in_db(db, country_code, user_ids, is_active)


@router.delete("/users/{country_code}/bulk")
def bulk_delete_users(country_code: str = Path(..., description="ISO country code"), payload: dict = Body(...), _: User = Depends(require_admin), db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    get_country_or_404(country_code.upper(), db)
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


@router.delete("/users/{country_code}/{user_id}")
def delete_user_permanent(country_code: str = Path(..., description="ISO country code"), user_id: int = Path(...), delete_orders: bool = Query(False), _: User = Depends(require_admin), db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    get_country_or_404(country_code.upper(), db)
    return delete_user_admin(user_id, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db, delete_orders=delete_orders)