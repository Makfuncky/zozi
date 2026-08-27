"""Admin catalog router — thin HTTP layer delegating to catalog domain services."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Path, Body
from sqlalchemy.orm import Session

from domains.catalog.services.categories.category_admin_read_service import list_categories_paginated
from domains.catalog.services.categories.category_service import (
    create_category,
    update_category_by_id,
    delete_category_by_id,
    reorder_categories,
    archive_category as archive_category_service,
    restore_category as restore_category_service,
    bulk_archive_categories as bulk_archive_categories_service,
    bulk_restore_categories as bulk_restore_categories_service,
    build_category_payload,
    build_category_updates,
)
from domains.catalog.services.products.admin_products_service import (
    list_all_products,
    approve_product,
    reject_product,
    update_product_badge,
    bulk_archive_products,
    bulk_restore_products,
    bulk_moderate_products,
    bulk_change_category,
    archive_product,
    restore_product_route,
    delete_product_permanent,
)
from infrastructure.database.database import get_db
from infrastructure.database.schemas import ArchiveRequest, BulkActionRequest, BulkCategoryChangeRequest
from infrastructure.security.dependencies import require_admin, require_super_admin
from rbac.dependencies import require_feature

router = APIRouter(prefix="/api/v1/admin/catalog", tags=["admin", "catalog"])


# ── Products ─────────────────────────────────────────────────────────────────


@router.get("/products/{country_code}", status_code=200, tags=["admin-products"])
def list_products(
    country_code: str = Path(..., description="ISO country code"),
    page: int = Query(1, ge=1),
    size: int = Query(50),
    moderation_status: str | None = None,
    include_deleted: bool = False,
    _=Depends(require_admin),
    db: Session = Depends(get_db),
):
    require_feature("catalog.list")
    return list_all_products(country_code, page, size, moderation_status, include_deleted, _, db)


@router.get("/products/{country_code}/pending", status_code=200, tags=["admin-products"])
def list_pending_products_route(
    country_code: str,
    page: int = Query(1),
    page_size: int = Query(50),
    _=Depends(require_admin),
    db: Session = Depends(get_db),
):
    require_feature("catalog.list")
    return list_all_products(country_code, page, page_size, "pending", False, _, db)


@router.put("/products/{country_code}/{product_id}/approve", status_code=200, tags=["admin-products"])
def approve_product_route(
    country_code: str = Path(..., description="ISO country code"),
    product_id: int = Path(...),
    _=Depends(require_admin),
    db: Session = Depends(get_db),
):
    require_feature("catalog.write")
    return approve_product(country_code, product_id, _, db)


@router.put("/products/{country_code}/{product_id}/reject", status_code=200, tags=["admin-products"])
def reject_product_route(
    country_code: str = Path(..., description="ISO country code"),
    product_id: int = Path(...),
    reason: str | None = None,
    _=Depends(require_admin),
    db: Session = Depends(get_db),
):
    require_feature("catalog.write")
    return reject_product(country_code, product_id, reason, _, db)


@router.patch("/products/{country_code}/{product_id}/badge", status_code=200, tags=["admin-products"])
def update_product_badge_route(
    country_code: str = Path(..., description="ISO country code"),
    product_id: int = Path(...),
    field: str = Body(...),
    value: bool = Body(...),
    _=Depends(require_admin),
    db: Session = Depends(get_db),
):
    require_feature("catalog.write")
    return update_product_badge(country_code, product_id, field, value, _, db)


@router.post("/products/{country_code}/bulk/archive", status_code=201, tags=["admin-products"])
def bulk_archive_products_route(
    country_code: str = Path(..., description="ISO country code"),
    payload: BulkActionRequest = Body(...),
    _=Depends(require_admin),
    db: Session = Depends(get_db),
):
    require_feature("catalog.write")
    return bulk_archive_products(country_code, payload, _, db)


@router.post("/products/{country_code}/bulk/restore", status_code=201, tags=["admin-products"])
def bulk_restore_products_route(
    country_code: str = Path(..., description="ISO country code"),
    payload: BulkActionRequest = Body(...),
    _=Depends(require_admin),
    db: Session = Depends(get_db),
):
    require_feature("catalog.write")
    return bulk_restore_products(country_code, payload, _, db)


@router.post("/products/{country_code}/bulk/moderate", status_code=201, tags=["admin-products"])
def bulk_moderate_products_route(
    country_code: str = Path(..., description="ISO country code"),
    payload: dict = Body(...),
    _=Depends(require_admin),
    db: Session = Depends(get_db),
):
    require_feature("catalog.write")
    return bulk_moderate_products(country_code, payload, _, db)


@router.post("/products/{country_code}/bulk/category-change", status_code=201, tags=["admin-products"])
def bulk_change_category_route(
    country_code: str = Path(..., description="ISO country code"),
    payload: BulkCategoryChangeRequest = Body(...),
    _=Depends(require_admin),
    db: Session = Depends(get_db),
):
    require_feature("catalog.category.manage")
    return bulk_change_category(country_code, payload, _, db)


@router.post("/products/{country_code}/{product_id}/archive", status_code=201, tags=["admin-products"])
def archive_product_route(
    country_code: str = Path(..., description="ISO country code"),
    product_id: int = Path(...),
    payload: ArchiveRequest | None = Body(None),
    _=Depends(require_admin),
    db: Session = Depends(get_db),
):
    require_feature("catalog.write")
    return archive_product(country_code, product_id, payload, _, db)


@router.post("/products/{country_code}/{product_id}/restore", status_code=201, tags=["admin-products"])
def restore_product_route_wrapper(
    country_code: str = Path(..., description="ISO country code"),
    product_id: int = Path(...),
    _=Depends(require_admin),
    db: Session = Depends(get_db),
):
    require_feature("catalog.write")
    return restore_product_route(country_code, product_id, _, db)


@router.delete("/products/{country_code}/{product_id}", status_code=200, tags=["admin-products"])
def delete_product_permanent_route(
    country_code: str = Path(..., description="ISO country code"),
    product_id: int = Path(...),
    _=Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    require_feature("catalog.delete")
    return delete_product_permanent(country_code, product_id, _, db)


# ── Categories ───────────────────────────────────────────────────────────────


@router.get("/categories/{country_code}", status_code=200, tags=["admin-categories"])
def list_categories_route(
    country_code: str = Path(..., description="ISO country code"),
    include_deleted: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    require_feature("catalog.list")
    return list_categories_paginated(
        db,
        country_code=country_code,
        include_deleted=include_deleted,
        page=page,
        page_size=page_size,
    )


@router.post("/categories/{country_code}", status_code=201, tags=["admin-categories"])
def create_category_route(
    country_code: str = Path(..., description="ISO country code"),
    name: str | None = Body(None),
    slug: str | None = Body(None),
    parent_id: int | None = Body(None),
    sort_order: int = Body(0),
    description: str | None = Body(None),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    require_feature("catalog.category.manage")
    payload = build_category_payload(
        name=name,
        slug=slug,
        parent_id=parent_id,
        sort_order=sort_order,
        description=description,
        country_code=country_code,
    )
    return create_category(db, payload, rebuild_paths=True)


@router.put("/categories/{country_code}/{category_id}", status_code=200, tags=["admin-categories"])
def update_category_route(
    country_code: str = Path(..., description="ISO country code"),
    category_id: int = Path(...),
    name: str | None = Body(None),
    slug: str | None = Body(None),
    parent_id: int | None = Body(None),
    sort_order: int | None = Body(None),
    description: str | None = Body(None),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    require_feature("catalog.category.manage")
    updates = build_category_updates(
        name=name,
        slug=slug,
        parent_id=parent_id,
        sort_order=sort_order,
        description=description,
    )
    return update_category_by_id(db, country_code, category_id, updates)


@router.post("/categories/{country_code}/{category_id}/archive", status_code=201, tags=["admin-categories"])
def archive_category_route(
    country_code: str = Path(..., description="ISO country code"),
    category_id: int = Path(...),
    payload: ArchiveRequest | None = Body(None),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    require_feature("catalog.category.manage")
    return archive_category_service(
        category_id,
        current_user,
        db,
        reason=payload.reason if payload else None,
    )


@router.post("/categories/{country_code}/{category_id}/restore", status_code=201, tags=["admin-categories"])
def restore_category_route(
    country_code: str = Path(..., description="ISO country code"),
    category_id: int = Path(...),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    require_feature("catalog.category.manage")
    return restore_category_service(category_id, current_user, db)


@router.post("/categories/{country_code}/reorder", status_code=201, tags=["admin-categories"])
def reorder_categories_route(
    country_code: str = Path(..., description="ISO country code"),
    order: dict | None = Body(None),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    require_feature("catalog.category.manage")
    return reorder_categories(db, order or {})


@router.post("/categories/{country_code}/bulk/archive", status_code=201, tags=["admin-categories"])
def bulk_archive_categories_route(
    country_code: str = Path(..., description="ISO country code"),
    payload: BulkActionRequest = Body(...),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    require_feature("catalog.category.manage")
    return bulk_archive_categories_service(payload.ids, current_user, db, reason=payload.reason)


@router.post("/categories/{country_code}/bulk/restore", status_code=201, tags=["admin-categories"])
def bulk_restore_categories_route(
    country_code: str = Path(..., description="ISO country code"),
    payload: BulkActionRequest = Body(...),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    require_feature("catalog.category.manage")
    return bulk_restore_categories_service(payload.ids, current_user, db)


@router.delete("/categories/{country_code}/{category_id}", status_code=200, tags=["admin-categories"])
def delete_category_route(
    country_code: str = Path(..., description="ISO country code"),
    category_id: int = Path(...),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    require_feature("catalog.category.manage")
    return delete_category_by_id(db, country_code, category_id)



