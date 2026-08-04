"""Admin products router."""
from fastapi import APIRouter, Depends, HTTPException, Query, Body, Path
from sqlalchemy.orm import Session
from data.db import get_db
from data.schemas import CursorPage, ArchiveRequest, BulkActionRequest, BulkCategoryChangeRequest
from data.models import Product, User
from utils.dependencies import require_admin, require_super_admin
from utils.country_rls import get_country_or_404
from data.controllers_admin_controller import archive_entity, restore_entity, bulk_archive_entities, bulk_restore_entities, hard_delete_entity, bulk_product_moderation, bulk_category_change
from data.catalog_product_utils import _bump_product_cache_version
from services.core.admin_router_service import (
    list_products_by_country, get_product_by_id, approve_product_in_db,
    reject_product_in_db, update_product_badge_in_db
)

router = APIRouter()


@router.get("/products/{country_code}", response_model=CursorPage)
def list_all_products(
    country_code: str = Path(..., description="ISO country code"),
    cursor: str | None = Query(None, description="Cursor for next page"),
    limit: int = Query(50, ge=1, le=100),
    moderation_status: str = None,
    include_deleted: bool = False,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    get_country_or_404(country_code.upper(), db)
    return list_products_by_country(db, country_code, cursor=cursor, limit=limit, moderation_status=moderation_status, include_deleted=include_deleted)


@router.put("/products/{country_code}/{product_id}/approve")
def approve_product(country_code: str = Path(..., description="ISO country code"), product_id: int = Path(...), _=Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    result = approve_product_in_db(db, country_code, product_id)
    _bump_product_cache_version()
    return result


@router.put("/products/{country_code}/{product_id}/reject")
def reject_product(country_code: str = Path(..., description="ISO country code"), product_id: int = Path(...), reason: str = None, _=Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    return reject_product_in_db(db, country_code, product_id, reason=reason)


@router.patch("/products/{country_code}/{product_id}/badge")
def update_product_badge_route(country_code: str = Path(..., description="ISO country code"), product_id: int = Path(...), field: str = Body(...), value: bool = Body(...), _=Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    result = update_product_badge_in_db(db, country_code, product_id, field=field, value=value)
    _bump_product_cache_version()
    return result


@router.post("/products/{country_code}/bulk/archive")
def bulk_archive_products(country_code: str = Path(..., description="ISO country code"), payload: BulkActionRequest = None, _=Depends(require_admin), db: Session = Depends(get_db), current_user=Depends(require_admin)):
    get_country_or_404(country_code.upper(), db)
    return bulk_archive_entities("product", payload.ids, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db, payload.reason)


@router.post("/products/{country_code}/bulk/restore")
def bulk_restore_products(country_code: str = Path(..., description="ISO country code"), payload: BulkActionRequest = None, _=Depends(require_admin), db: Session = Depends(get_db), current_user=Depends(require_admin)):
    get_country_or_404(country_code.upper(), db)
    return bulk_restore_entities("product", payload.ids, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db)


@router.post("/products/{country_code}/bulk/moderate")
def bulk_moderate_products(country_code: str = Path(..., description="ISO country code"), payload: dict = Body(...), _=Depends(require_admin), db: Session = Depends(get_db), current_user=Depends(require_admin)):
    get_country_or_404(country_code.upper(), db)
    product_ids = payload.get("product_ids", [])
    action = payload.get("action")
    if not product_ids or action not in ("approve", "reject"):
        raise HTTPException(400, "product_ids and action (approve/reject) are required")
    return bulk_product_moderation(product_ids, action, payload.get("note"), {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db)


@router.post("/products/{country_code}/bulk/category-change")
def bulk_change_category(country_code: str = Path(..., description="ISO country code"), payload: BulkCategoryChangeRequest = None, _=Depends(require_admin), db: Session = Depends(get_db), current_user=Depends(require_admin)):
    get_country_or_404(country_code.upper(), db)
    return bulk_category_change(payload.ids, payload.category_id, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db, payload.reason)


@router.post("/products/{country_code}/{product_id}/archive")
def archive_product(country_code: str = Path(..., description="ISO country code"), product_id: int = Path(...), payload: ArchiveRequest = None, _=Depends(require_admin), db: Session = Depends(get_db), current_user=Depends(require_admin)):
    get_country_or_404(country_code.upper(), db)
    return archive_entity("product", product_id, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db, payload.reason if payload else None)


@router.post("/products/{country_code}/{product_id}/restore")
def restore_product_route(country_code: str = Path(..., description="ISO country code"), product_id: int = Path(...), _=Depends(require_admin), db: Session = Depends(get_db), current_user=Depends(require_admin)):
    get_country_or_404(country_code.upper(), db)
    return restore_entity("product", product_id, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db)


@router.delete("/products/{country_code}/{product_id}")
def delete_product_permanent(country_code: str = Path(..., description="ISO country code"), product_id: int = Path(...), _=Depends(require_super_admin), db: Session = Depends(get_db), current_user=Depends(require_super_admin)):
    get_country_or_404(country_code.upper(), db)
    return hard_delete_entity("product", product_id, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db)
