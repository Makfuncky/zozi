"""Admin catalog router — canonical."""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status

from .categories import router as categories_router
from .products import router as products_router
from .search import router as search_router
from __future__ import annotations
from domains.accounts.services.permissions.permission_service import create_category
from domains.accounts.services.permissions.permission_service import create_category as create_category_model
from domains.accounts.services.permissions.permission_service import create_category as svc_create_category
from domains.accounts.services.permissions.permission_service import delete_category
from domains.accounts.services.permissions.permission_service import delete_category as delete_category_model
from domains.accounts.services.permissions.permission_service import delete_category as svc_delete_category
from domains.accounts.services.permissions.permission_service import list_categories
from domains.accounts.services.permissions.permission_service import update_category
from domains.accounts.services.permissions.permission_service import update_category as svc_update_category
from domains.accounts.services.permissions.permission_service import update_category as update_category_model
from domains.catalog.models.ai_upload import AIGenerationLog
from domains.catalog.models.ai_upload import AIStagingProduct
from domains.catalog.models.ai_upload import AIStagingVariant
from domains.catalog.models.ai_upload import AIUploadJob
from domains.catalog.models.products import Category
from domains.catalog.models.products import Product
from domains.catalog.models.products import ProductVariant
from domains.catalog.services.categories.admin_categories_service import archive_category
from domains.catalog.services.categories.admin_categories_service import bulk_archive_categories
from domains.catalog.services.categories.admin_categories_service import bulk_restore_categories
from domains.catalog.services.categories.admin_categories_service import reorder_categories
from domains.catalog.services.categories.admin_categories_service import reorder_categories as reorder_categories_model
from domains.catalog.services.categories.admin_categories_service import reorder_categories as svc_reorder_categories
from domains.catalog.services.categories.admin_categories_service import restore_category
from domains.catalog.services.categories.category_admin_read_service import list_categories_paginated
from domains.catalog.services.categories.category_service import rebuild_category_paths
from domains.catalog.services.products.admin_products_service import approve_product_route
from domains.catalog.services.products.admin_products_service import bulk_delete_products_route
from domains.catalog.services.products.admin_products_service import bulk_product_moderation
from domains.catalog.services.products.admin_products_service import list_pending_products
from domains.catalog.services.products.admin_products_service import reject_product_route
from domains.catalog.services.products.admin_products_service import toggle_product_badge_route
from domains.catalog.services.products.admin_products_service import unarchive_product_route
from domains.catalog.services.products.bulk_ops_write_service import bulk_archive_entities
from domains.catalog.services.products.bulk_ops_write_service import bulk_restore_entities
from domains.catalog.services.products.products_service import _bump_product_cache_version
from domains.catalog.services.search.ai_search_service import AISearchService
from domains.catalog.services.search.search_service import AdvancedFilterService
from domains.catalog.services.search.search_service import AdvancedSearchEngine
from domains.country.utils.country_rls import get_country_or_404
from domains.governance.models.user import User
from domains.governance.services.admin.bulk_ops_service import bulk_category_change
from domains.governance.services.settings.misc_service import archive_entity
from domains.governance.services.settings.misc_service import hard_delete_entity
from domains.governance.services.settings.misc_service import restore_entity
from domains.media.services.ai import ai_service
from domains.security.services.iam.security_dependencies import require_roles
from infrastructure.database.database import get_db
from infrastructure.database.database import get_db_context
from infrastructure.database.schemas import ArchiveRequest
from infrastructure.database.schemas import ArchiveRequest, BulkActionRequest
from infrastructure.database.schemas import ArchiveRequest, BulkActionRequest, BulkCategoryChangeRequest
from infrastructure.database.schemas import BulkActionRequest
from infrastructure.routing.route_contract import delete, get, post, put
from infrastructure.search.routers import get_recommendations
from infrastructure.search.routers import smart_search
from infrastructure.utils.config import BASE_DIR
from infrastructure.utils.dependencies import require_admin
from infrastructure.utils.dependencies import require_admin, require_super_admin
from infrastructure.utils.pagination import paginated_response
from infrastructure.utils.rls_interceptor import clear_rls_context, set_rls_context
from infrastructure.utils.rls_interceptor import set_rls_context, clear_rls_context
from infrastructure.utils.storage import storage as _storage
from infrastructure.utils.variant_key import compute_variant_key
from providers.image import process_image_search
from providers.voice import transcribe_audio
from rbac import get_current_user
from rbac import get_optional_user
from services import ai_service
from sqlalchemy.orm import Session
from typing import Any, Dict, Optional
from typing import Optional
import json
import logging
import logging as _l; _l.getLogger(__name__).warning("skip categories_router: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip products_router: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip search_router: %s", _e)
import os
import uuid

router = APIRouter(prefix="/api/v1/admin/catalog", tags=["admin", "catalog"])

@router.get("/products/{country_code}/pending", status_code=200, tags=['admin-products'])
def list_pending_products_route(
    country_code: str,
    page: int = Query(1),
    page_size: int = Query(50),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)


@router.post("/products/{country_code}/{product_id}/approve", status_code=201, tags=['admin-products'])
def approve_product_route_route(
    country_code: str,
    product_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)


@router.post("/products/{country_code}/{product_id}/reject", status_code=201, tags=['admin-products'])
def reject_product_route_route(
    country_code: str,
    product_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    note: Optional[str] = Body(None)


@router.post("/products/{country_code}/{product_id}/badge", status_code=201, tags=['admin-products'])
def toggle_product_badge_route_route(
    country_code: str,
    product_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    field: str = Body('is_featured', embed=True),
    value: bool = Body(True, embed=True)


@router.post("/products/{country_code}/bulk/delete", status_code=201, tags=['admin-products'])
def bulk_delete_products_route_route(
    country_code: str,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    ids: list[int] = Body(None)


@router.post("/products/{country_code}/{product_id}/unarchive", status_code=201, tags=['admin-products'])
def unarchive_product_route_route(
    country_code: str,
    product_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)


@router.get("/categories/{country_code}", status_code=200, tags=['admin-categories'])
def list_categories_route(
    country_code: str,
    include_deleted: bool = Query(False),
    page: int = Query(1),
    page_size: int = Query(20),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)


@router.post("/categories/{country_code}", status_code=201, tags=['admin-categories'])
def create_category_route(
    country_code: str,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    name: Optional[str] = Body(None),
    slug: Optional[str] = Body(None),
    parent_id: Optional[int] = Body(None),
    sort_order: int = Body(0),
    description: Optional[str] = Body(None)


@router.put("/categories/{country_code}/{category_id}", status_code=200, tags=['admin-categories'])
def update_category_route(
    country_code: str,
    category_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    name: Optional[str] = Body(None),
    slug: Optional[str] = Body(None),
    parent_id: Optional[int] = Body(None),
    sort_order: Optional[int] = Body(None),
    description: Optional[str] = Body(None)


@router.post("/categories/{country_code}/{category_id}/archive", status_code=201, tags=['admin-categories'])
def archive_category_route(
    country_code: str,
    category_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    payload: ArchiveRequest = Body(...)


@router.post("/categories/{country_code}/{category_id}/restore", status_code=201, tags=['admin-categories'])
def restore_category_route(
    country_code: str,
    category_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)


@router.post("/categories/{country_code}/reorder", status_code=201, tags=['admin-categories'])
def reorder_categories_route(
    country_code: str,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    order: Optional[dict] = Body(None)


@router.post("/categories/{country_code}/bulk/archive", status_code=201, tags=['admin-categories'])
def bulk_archive_categories_route(
    country_code: str,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    payload: BulkActionRequest = Body(...)


@router.post("/categories/{country_code}/bulk/restore", status_code=201, tags=['admin-categories'])
def bulk_restore_categories_route(
    country_code: str,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    payload: BulkActionRequest = Body(...)


@router.delete("/categories/{country_code}/{category_id}", status_code=200, tags=['admin-categories'])
def delete_category_route(
    country_code: str,
    category_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)


@router.get("/products/{country_code}")
def list_all_products(country_code: str = Path(..., description="ISO country code"), page: int = Query(1, ge=1), size: int = Query(50), moderation_status: str = None, include_deleted: bool = False, _=Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        q = db.query(Product).filter(Product.country_code == country_code.upper())
        if moderation_status: q = q.filter(Product.moderation_status == moderation_status)
        if not include_deleted: q = q.filter(Product.is_deleted == False)
        return paginated_response(q, page, size)
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
        db.commit()
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
        db.commit()
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
        db.commit()
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




@router.get("/categories/{country_code}")
def list_categories(country_code: str = Path(..., description="ISO country code"), include_deleted: bool = False, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), _: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        q = db.query(Category).filter(Category.country_code == country_code.upper())
        if not include_deleted: q = q.filter(Category.is_active == True)
        total = q.count()
        rows = q.order_by(Category.sort_order).offset((page - 1) * page_size).limit(page_size).all()
        return {"data": rows, "total": total, "page": page, "page_size": page_size}
    finally:
        clear_rls_context()




@router.post("/categories/{country_code}")
def create_category(country_code: str = Path(..., description="ISO country code"), name: str = None, slug: str = None, parent_id: int = None, sort_order: int = 0, description: str = None, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        cat_data = {
            "name": name,
            "slug": slug,
            "parent_id": parent_id,
            "sort_order": sort_order,
            "description": description,
            "country_code": country_code.upper(),
        }
        cat = create_category_model(db, **cat_data)
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
        cat = update_category_model(db, cat, updates)
        rebuild_category_paths(db)
        return cat
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
        reorder_categories_model(db, {int(k): v for k, v in order.items()})
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
        delete_category_model(db, cat)
        return {"message": "Category deleted"}
    finally:
        clear_rls_context()




@router.get("/products/{country_code}")
def list_all_products(country_code: str = Path(..., description="ISO country code"), page: int = Query(1, ge=1), size: int = Query(50), moderation_status: str = None, include_deleted: bool = False, _=Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        q = db.query(Product).filter(Product.country_code == country_code.upper())
        if moderation_status: q = q.filter(Product.moderation_status == moderation_status)
        if not include_deleted: q = q.filter(Product.is_deleted == False)
        return paginated_response(q, page, size)
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
        db.commit()
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
        db.commit()
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
        db.commit()
        _bump_product_cache_version()
        return {"message": "Product badge updated", "field": field, "value": value}
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




@router.post("/jobs", status_code=201)
async def create_ai_upload_job(
    background_tasks: BackgroundTasks,
    images: list[UploadFile] = File(default=[]),
    country_code: str = Form(...),
    model_used: Optional[str] = Form(None),
    prompt_hash: Optional[str] = Form(None),
    current_user: dict = _AUTH,
    db: Session = Depends(get_db),
):
    if not images:
        raise HTTPException(status_code=422, detail="At least one image is required.")

    user_id = current_user.get("id") or current_user.get("user_id")
    if user_id is None and isinstance(current_user.get("user"), dict):
        user_id = current_user["user"].get("id")

    job = AIUploadJob(
        supplier_id=int(user_id),
        status="pending",
        model_used=model_used,
        prompt_hash=prompt_hash,
        source_media_json="[]",
        country_code=country_code,
    )
    db.add(job)
    db.flush()

    media_list = []
    for img in images:
        try:
            key, url, content = _save_upload(img, str(job.id))
            media_list.append({"filename": img.filename, "key": key, "url": url})
        except Exception as exc:
            logger.warning("Failed to save upload %s: %s", img.filename, exc)
    job.source_media_json = json.dumps(media_list)

    if not media_list:
        raise HTTPException(status_code=422, detail="No images could be saved.")

    db.commit()
    db.refresh(job)

    background_tasks.add_task(process_ai_upload_job, job.id)
    return {
        "job_id": job.id,
        "status": job.status,
        "country_code": job.country_code,
        "media_count": len(media_list),
    }


@router.get("/jobs/{job_id}")
def get_ai_upload_job(job_id: int, current_user: dict = _AUTH, db: Session = Depends(get_db)):
    job = db.get(AIUploadJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")
    staging = db.query(AIStagingProduct).filter(AIStagingProduct.job_id == job_id).all()
    logs = db.query(AIGenerationLog).filter(AIGenerationLog.job_id == job_id).all()
    return {
        "job": {
            "id": job.id,
            "status": job.status,
            "model_used": job.model_used,
            "tokens_used": float(job.tokens_used) if job.tokens_used is not None else None,
            "error_log": job.error_log,
            "country_code": job.country_code,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "created_product_id": job.created_product_id,
        },
        "staging_products": [
            {
                "id": s.id,
                "name": s.name,
                "description": s.description,
                "category": s.category,
                "color": s.color,
                "brand": s.brand,
                "price": float(s.price) if s.price is not None else None,
                "tags": s.tags,
                "sizes": s.sizes,
                "materials": s.materials,
                "image_url": s.image_url,
                "confidence_score": float(s.confidence_score) if s.confidence_score is not None else None,
                "requires_human_review": s.requires_human_review,
            }
            for s in staging
        ],
        "logs": [{"field": lg.field, "model_used": lg.model_used, "confidence": float(lg.confidence) if lg.confidence is not None else None} for lg in logs],
    }




@router.post("/jobs/{job_id}/publish", status_code=200)
def publish_ai_upload_job(
    job_id: int,
    overrides: Optional[dict] = None,
    current_user: dict = _AUTH,
    db: Session = Depends(get_db),


@router.post("/jobs/{job_id}/cancel", status_code=200)
def cancel_ai_upload_job(job_id: int, current_user: dict = _AUTH, db: Session = Depends(get_db)):
    job = db.get(AIUploadJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")
    if job.status in ("completed",):
        raise HTTPException(status_code=409, detail="Job already completed.")
    job.status = "cancelled"
    db.commit()
    return {"job_id": job.id, "status": "cancelled"}




@router.post("/voice")
async def voice_search(
    audio: UploadFile = File(None),
    text: str = Form(None),
    db: Session = Depends(get_db),
):
    """
    Voice search — accepts raw audio (transcribed via Whisper) OR pre-transcribed text.

    The frontend Web Speech API can send the transcript as `text` directly.
    For server-side whisper transcription, send the audio file as `audio`.

    Returns the transcript so the client can pass it to GET /search/filtered.
    """
    if text:
        transcript = text.strip()
    elif audio:
        audio_bytes = await audio.read()
        if not audio_bytes:
            raise HTTPException(status_code=400, detail="Empty audio file")
        transcript = transcribe_audio(audio_bytes) or ""
        if not transcript.strip():
            raise HTTPException(status_code=400, detail="Could not transcribe audio")
    else:
        raise HTTPException(
            status_code=400,
            detail="Provide either 'audio' (file upload) or 'text' (transcript string)",
        )

    # Parse the transcript through the NLP engine for structured intent
    engine = AdvancedSearchEngine(db)
    parsed = engine.parse_query(transcript)

    return {
        "transcript": transcript,
        "parsed_query": parsed,
    }


@router.get("")
def search(
    response: Response,
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),


@router.get("/products")
def search_products(
    response: Response,
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=50),
    supplier_id: int | None = None,
    db: Session = Depends(get_db),


@router.get("/recommendations")
def recommendations(
    limit: int = Query(8, ge=1, le=24),
    recent_categories: str | None = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),


@router.get("/recommendations/public")
def public_recommendations(
    limit: int = Query(8, ge=1, le=24),
    recent_categories: str | None = None,
    current_user: dict | None = Depends(get_optional_user),
    db: Session = Depends(get_db),


@router.get("/filters")
def get_available_filters(
    response: Response,
    category_id: int | None = Query(None),
    q: str | None = Query(None),
    db: Session = Depends(get_db),


@router.get("/filters/summary")
def get_filters_summary(
    response: Response,
    category_id: int | None = Query(None),
    q: str | None = Query(None),
    db: Session = Depends(get_db),


@router.get("/advanced")
def advanced_search_endpoint(
    q: str = Query(..., min_length=1),
    category_id: Optional[int] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    brands: Optional[str] = Query(None),
    min_rating: Optional[float] = Query(None),
    has_video: bool = Query(False),
    sort_by: str = Query("relevance", pattern="^(relevance|price_asc|price_desc|rating|newest)$"),
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),


@router.get("/ai")
def ai_powered_search(
    q: str = Query(..., min_length=1),
    category_id: Optional[int] = Query(None),
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),


@router.get("/autocomplete")
def autocomplete(
    q: str = Query(..., min_length=2),
    limit: int = Query(10, ge=1, le=20),
    db: Session = Depends(get_db),


@router.post("/visual")
async def visual_search(
    image: UploadFile = File(...),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """
    Visual similarity search — upload an image and find visually similar products.

    Accepts an image file, processes it through the AI image service,
    and returns visually similar products ranked by similarity score.
    """
    image_bytes = await image.read()
    result = await process_image_search(image_bytes=image_bytes, db=db, limit=limit)
    return result


@router.get("/trending")
def get_trending_searches(
    limit: int = Query(10, ge=1, le=20),
    db: Session = Depends(get_db),


@router.get("/fuzzy")
def fuzzy_search(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=50),
    cutoff: float = Query(0.6, ge=0.0, le=1.0),
    db: Session = Depends(get_db),


@router.get("/predict")
def get_word_predictions(
    q: str = Query(..., min_length=1),
    limit: int = Query(5, ge=1, le=10),
    db: Session = Depends(get_db),


@router.post("/filtered")
def get_filtered_products(
    filters: Dict[str, Any],
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),


@router.post("/jobs", status_code=201)
async def create_ai_upload_job(
    background_tasks: BackgroundTasks,
    images: list[UploadFile] = File(default=[]),
    country_code: str = Form(...),
    model_used: Optional[str] = Form(None),
    prompt_hash: Optional[str] = Form(None),
    current_user: dict = _AUTH,
    db: Session = Depends(get_db),
):
    if not images:
        raise HTTPException(status_code=422, detail="At least one image is required.")

    user_id = current_user.get("id") or current_user.get("user_id")
    if user_id is None and isinstance(current_user.get("user"), dict):
        user_id = current_user["user"].get("id")

    job = AIUploadJob(
        supplier_id=int(user_id),
        status="pending",
        model_used=model_used,
        prompt_hash=prompt_hash,
        source_media_json="[]",
        country_code=country_code,
    )
    db.add(job)
    db.flush()

    media_list = []
    for img in images:
        try:
            key, url, content = _save_upload(img, str(job.id))
            media_list.append({"filename": img.filename, "key": key, "url": url})
        except Exception as exc:
            logger.warning("Failed to save upload %s: %s", img.filename, exc)
    job.source_media_json = json.dumps(media_list)

    if not media_list:
        raise HTTPException(status_code=422, detail="No images could be saved.")

    db.commit()
    db.refresh(job)

    background_tasks.add_task(process_ai_upload_job, job.id)
    return {
        "job_id": job.id,
        "status": job.status,
        "country_code": job.country_code,
        "media_count": len(media_list),
    }


@router.get("/jobs/{job_id}")
def get_ai_upload_job(job_id: int, current_user: dict = _AUTH, db: Session = Depends(get_db)):
    job = db.get(AIUploadJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")
    staging = db.query(AIStagingProduct).filter(AIStagingProduct.job_id == job_id).all()
    logs = db.query(AIGenerationLog).filter(AIGenerationLog.job_id == job_id).all()
    return {
        "job": {
            "id": job.id,
            "status": job.status,
            "model_used": job.model_used,
            "tokens_used": float(job.tokens_used) if job.tokens_used is not None else None,
            "error_log": job.error_log,
            "country_code": job.country_code,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "created_product_id": job.created_product_id,
        },
        "staging_products": [
            {
                "id": s.id,
                "name": s.name,
                "description": s.description,
                "category": s.category,
                "color": s.color,
                "brand": s.brand,
                "price": float(s.price) if s.price is not None else None,
                "tags": s.tags,
                "sizes": s.sizes,
                "materials": s.materials,
                "image_url": s.image_url,
                "confidence_score": float(s.confidence_score) if s.confidence_score is not None else None,
                "requires_human_review": s.requires_human_review,
            }
            for s in staging
        ],
        "logs": [{"field": lg.field, "model_used": lg.model_used, "confidence": float(lg.confidence) if lg.confidence is not None else None} for lg in logs],
    }




@router.post("/jobs/{job_id}/publish", status_code=200)
def publish_ai_upload_job(
    job_id: int,
    overrides: Optional[dict] = None,
    current_user: dict = _AUTH,
    db: Session = Depends(get_db),


@router.post("/jobs/{job_id}/cancel", status_code=200)
def cancel_ai_upload_job(job_id: int, current_user: dict = _AUTH, db: Session = Depends(get_db)):
    job = db.get(AIUploadJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")
    if job.status in ("completed",):
        raise HTTPException(status_code=409, detail="Job already completed.")
    job.status = "cancelled"
    db.commit()
    return {"job_id": job.id, "status": "cancelled"}



