"""Admin categories router."""
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from data.db import get_db
from data.schemas import CursorPage
from data.models import Category, User
from data.schemas import ArchiveRequest, BulkActionRequest
from utils.dependencies import require_admin
from utils.pagination import cursor_paginate_desc
from utils.country_rls import get_country_or_404
from utils.rls_interceptor import set_rls_context, clear_rls_context
from utils.category_tree import rebuild_category_paths
from services.core.admin_operations_service import archive_entity, restore_entity, bulk_archive_entities, bulk_restore_entities
from services.products_write_service import (
    create_category as create_category_db,
    update_category as update_category_db,
    delete_category as delete_category_db,
    update_category_sort_order as update_category_sort_order_db,
    reorder_categories as reorder_categories_db,
)

router = APIRouter()


@router.get("/categories/{country_code}", response_model=CursorPage)
def list_categories(
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
        q = db.query(Category).filter(Category.country_code == country_code.upper())
        if not include_deleted:
            q = q.filter(Category.is_active == True)
        return cursor_paginate_desc(q, cursor=cursor, page_size=limit)
    finally:
        clear_rls_context()


@router.post("/categories/{country_code}")
def create_category(country_code: str = Path(..., description="ISO country code"), name: str = None, slug: str = None, parent_id: int = None, sort_order: int = 0, description: str = None, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        cat = create_category_db(db, name=name, slug=slug, parent_id=parent_id, sort_order=sort_order, description=description, country_code=country_code.upper())
        rebuild_category_paths(db)
        return cat
    finally:
        clear_rls_context()


@router.put("/categories/{country_code}/{category_id}")
def update_category(country_code: str = Path(..., description="ISO country code"), category_id: int = Path(...), name: str = None, slug: str = None, parent_id: int = None, sort_order: int = None, description: str = None, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        cat = db.query(Category).filter(Category.id == category_id, Category.country_code == country_code.upper()).first()
        if not cat: raise HTTPException(404)
        updates = {}
        if name is not None: updates["name"] = name
        if slug is not None: updates["slug"] = slug
        if parent_id is not None: updates["parent_id"] = parent_id
        if sort_order is not None: updates["sort_order"] = sort_order
        if description is not None: updates["description"] = description
        result = update_category_db(db, cat, updates)
        rebuild_category_paths(db)
        return result
    finally:
        clear_rls_context()


@router.post("/categories/{country_code}/{category_id}/archive")
def archive_category(country_code: str = Path(..., description="ISO country code"), category_id: int = Path(...), payload: ArchiveRequest = None, _: User = Depends(require_admin), db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return archive_entity("category", category_id, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db, payload.reason if payload else None)
    finally:
        clear_rls_context()


@router.post("/categories/{country_code}/{category_id}/restore")
def restore_category(country_code: str = Path(..., description="ISO country code"), category_id: int = Path(...), _: User = Depends(require_admin), db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return restore_entity("category", category_id, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db)
    finally:
        clear_rls_context()


@router.post("/categories/{country_code}/reorder")
def reorder_categories(country_code: str = Path(..., description="ISO country code"), order: dict = None, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        category_updates = {int(cid): pos for cid, pos in order.items()}
        reorder_categories_db(db, category_updates, country_code.upper())
        return {"message": "Categories reordered"}
    finally:
        clear_rls_context()


@router.post("/categories/{country_code}/bulk/archive")
def bulk_archive_categories(country_code: str = Path(..., description="ISO country code"), payload: BulkActionRequest = None, _: User = Depends(require_admin), db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return bulk_archive_entities("category", payload.ids, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db, payload.reason)
    finally:
        clear_rls_context()


@router.post("/categories/{country_code}/bulk/restore")
def bulk_restore_categories(country_code: str = Path(..., description="ISO country code"), payload: BulkActionRequest = None, _: User = Depends(require_admin), db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return bulk_restore_entities("category", payload.ids, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db)
    finally:
        clear_rls_context()


@router.delete("/categories/{country_code}/{category_id}")
def delete_category(country_code: str = Path(..., description="ISO country code"), category_id: int = Path(...), _: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        cat = db.query(Category).filter(Category.id == category_id, Category.country_code == country_code.upper()).first()
        if not cat: raise HTTPException(404)
        delete_category_db(db, cat)
        return {"message": "Category deleted"}
    finally:
        clear_rls_context()