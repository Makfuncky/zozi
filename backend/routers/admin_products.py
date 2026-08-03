"""Admin products router."""
from fastapi import APIRouter, Depends, HTTPException, Query, Body, Path
from sqlalchemy.orm import Session
from data.db import get_db
from data.schemas import CursorPage, ArchiveRequest, BulkActionRequest, BulkCategoryChangeRequest
from data.models import Product, User
from utils.dependencies import require_admin, require_super_admin
from utils.country_rls import get_country_or_404
from utils.rls_interceptor import set_rls_context, clear_rls_context
from utils.pagination import cursor_paginate_desc
from data.controllers_admin_controller import archive_entity, restore_entity, bulk_archive_entities, bulk_restore_entities, hard_delete_entity, bulk_product_moderation, bulk_category_change
from services.catalog.product_utils import _bump_product_cache_version

from services.write_helpers import commit_only
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
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        q = db.query(Product).filter(Product.country_code == country_code.upper())
        if moderation_status:
            q = q.filter(Product.moderation_status == moderation_status)
        if not include_deleted:
            q = q.filter(Product.is_deleted == False)
        return cursor_paginate_desc(q, cursor=cursor, page_size=limit)
    finally:
        clear_rls_context()


@router.put("/products/{country_code}/{product_id}/approve")
def approve_product(country_code: str = Path(..., description="ISO country code"), product_id: int = Path(...), _=Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        p = db.query(Product).filter(Product.id == product_id, Product.country_code == country_code.upper()).first()
        if not p: raise HTTPException(404)
        p.moderation_status = "approved"; p.is_verified = True
        commit_only(db)
        _bump_product_cache_version()
        return {"message": "Product approved"}
    finally:
        clear_rls_context()


@router.put("/products/{country_code}/{product_id}/reject")
def reject_product(country_code: str = Path(..., description="ISO country code"), product_id: int = Path(...), reason: str = None, _=Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        p = db.query(Product).filter(Product.id == product_id, Product.country_code == country_code.upper()).first()
        if not p: raise HTTPException(404)
        p.moderation_status = "rejected"; p.moderation_notes = reason
        commit_only(db)
        _bump_product_cache_version()
        return {"message": "Product rejected"}
    finally:
        clear_rls_context()


@router.patch("/products/{country_code}/{product_id}/badge")
def update_product_badge(country_code: str = Path(..., description="ISO country code"), product_id: int = Path(...), field: str = Body(...), value: bool = Body(...), _=Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        p = db.query(Product).filter(Product.id == product_id, Product.country_code == country_code.upper()).first()
        if not p: raise HTTPException(404)
        if field not in ("is_hot", "is_featured"):
            raise HTTPException(400, "field must be 'is_hot' or 'is_featured'")
        setattr(p, field, value)
        commit_only(db)
        _bump_product_cache_version()
        return {"message": f"Product badge updated", "field": field, "value": value}
    finally:
        clear_rls_context()


@router.post("/products/{country_code}/bulk/archive")
def bulk_archive_products(country_code: str = Path(..., description="ISO country code"), payload: BulkActionRequest = None, _=Depends(require_admin), db: Session = Depends(get_db), current_user=Depends(require_admin)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return bulk_archive_entities("product", payload.ids, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db, payload.reason)
    finally:
        clear_rls_context()


@router.post("/products/{country_code}/bulk/restore")
def bulk_restore_products(country_code: str = Path(..., description="ISO country code"), payload: BulkActionRequest = None, _=Depends(require_admin), db: Session = Depends(get_db), current_user=Depends(require_admin)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return bulk_restore_entities("product", payload.ids, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db)
    finally:
        clear_rls_context()


@router.post("/products/{country_code}/bulk/moderate")
def bulk_moderate_products(country_code: str = Path(..., description="ISO country code"), payload: dict = Body(...), _=Depends(require_admin), db: Session = Depends(get_db), current_user=Depends(require_admin)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        product_ids = payload.get("product_ids", [])
        action = payload.get("action")
        if not product_ids or action not in ("approve", "reject"):
            raise HTTPException(400, "product_ids and action (approve/reject) are required")
        return bulk_product_moderation(product_ids, action, payload.get("note"), {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db)
    finally:
        clear_rls_context()


@router.post("/products/{country_code}/bulk/category-change")
def bulk_change_category(country_code: str = Path(..., description="ISO country code"), payload: BulkCategoryChangeRequest = None, _=Depends(require_admin), db: Session = Depends(get_db), current_user=Depends(require_admin)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return bulk_category_change(payload.ids, payload.category_id, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db, payload.reason)
    finally:
        clear_rls_context()


@router.post("/products/{country_code}/{product_id}/archive")
def archive_product(country_code: str = Path(..., description="ISO country code"), product_id: int = Path(...), payload: ArchiveRequest = None, _=Depends(require_admin), db: Session = Depends(get_db), current_user=Depends(require_admin)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return archive_entity("product", product_id, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db, payload.reason if payload else None)
    finally:
        clear_rls_context()


@router.post("/products/{country_code}/{product_id}/restore")
def restore_product_route(country_code: str = Path(..., description="ISO country code"), product_id: int = Path(...), _=Depends(require_admin), db: Session = Depends(get_db), current_user=Depends(require_admin)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return restore_entity("product", product_id, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db)
    finally:
        clear_rls_context()


@router.delete("/products/{country_code}/{product_id}")
def delete_product_permanent(country_code: str = Path(..., description="ISO country code"), product_id: int = Path(...), _=Depends(require_super_admin), db: Session = Depends(get_db), current_user=Depends(require_super_admin)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return hard_delete_entity("product", product_id, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db)
    finally:
        clear_rls_context()

