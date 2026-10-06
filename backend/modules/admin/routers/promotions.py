from __future__ import annotations

"""Admin promotions router — canonical."""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from sqlalchemy.orm import Session
from typing import Optional

from infrastructure.database.database import get_db
from infrastructure.security.dependencies import require_admin
from rbac.dependencies import require_feature
from domains.promotions.services.banners.banner_service import (
    BannerCreate,
    BannerUpdate,
    get_banners,
    get_banners_page,
)
from domains.promotions.services.admin_promotion_service import (
    create_banner as create_banner_controller,
    delete_banner as delete_banner_controller,
    update_banner as update_banner_controller,
)
from domains.promotions.services.engine.admin_promotions_write_service import (
    create_flash_sale,
    update_flash_sale,
    list_flash_sales,
)
from domains.governance.services.settings.misc_service import (
    archive_entity as archive_flash_sale_controller,
    restore_entity as restore_flash_sale_controller,
)
from infrastructure.utils.country_rls import get_country_or_404
from infrastructure.database.rls_interceptor import set_rls_context, clear_rls_context

router = APIRouter(prefix="/admin/promotions", tags=["admin", "promotions"])


@router.get("/banners/{country_code}")
def list_banners(
    country_code: str = Path(..., description="ISO country code"),
    position: str = None,
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("promotions.banners.read")),
):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return get_banners(db, banner_type=position, active_only=True)
    finally:
        clear_rls_context()


@router.get("/banners/{country_code}/all")
def list_all_banners(
    country_code: str = Path(..., description="ISO country code"),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("promotions.banners.read")),
):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return get_banners_page(db, active_only=False)
    finally:
        clear_rls_context()


@router.post("/banners/{country_code}", status_code=201)
def create_banner(
    country_code: str = Path(..., description="ISO country code"),
    payload: BannerCreate = Body(...),
    admin: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("promotions.banners.write")),
):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return create_banner_controller(payload, admin, db)
    finally:
        clear_rls_context()


@router.put("/banners/{country_code}/{banner_id}")
def update_banner(
    country_code: str = Path(..., description="ISO country code"),
    banner_id: int = Path(...),
    payload: BannerUpdate = Body(...),
    admin: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("promotions.banners.write")),
):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return update_banner_controller(banner_id, payload, admin, db)
    finally:
        clear_rls_context()


@router.delete("/banners/{country_code}/{banner_id}")
def delete_banner(
    country_code: str = Path(..., description="ISO country code"),
    banner_id: int = Path(...),
    admin: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("promotions.banners.write")),
):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return delete_banner_controller(banner_id, admin, db)
    finally:
        clear_rls_context()


@router.get("/admin_promotions_routes/health")
def health(_: dict = Depends(require_admin),
    _rf_gate: None = Depends(require_feature("promotions.banners.read"))
):
    return {"status": "ok", "router": "admin_promotions_routes", "prefix": "/api/v1/promotions"}


# ── Flash Sales (frontend-facing /admin/promotions/flash-sales aliases) ──────


@router.get("/flash-sales")
def list_flash_sales_route(
    include_deleted: bool = False,
    country_code: str | None = Query(None, description="ISO country code or '*' for all"),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("promotions.promotions.read")),
):
    items = list_flash_sales(db, include_deleted=include_deleted, country=country_code)
    return [
        {
            "id": item.id,
            "title": item.title,
            "description": item.description,
            "starts_at": item.starts_at.isoformat() if item.starts_at else None,
            "ends_at": item.ends_at.isoformat() if item.ends_at else None,
            "discount_pct": float(item.discount_pct) if item.discount_pct else 0,
            "is_active": item.is_active,
            "country_code": item.country_code,
            "is_deleted": item.is_deleted,
            "created_at": item.created_at.isoformat() if item.created_at else None,
            "updated_at": item.updated_at.isoformat() if item.updated_at else None,
        }
        for item in items
    ]


@router.post("/flash-sales", status_code=201)
def create_flash_sale_route(
    payload: dict = Body(...),
    admin: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("promotions.promotions.write")),
):
    sale = create_flash_sale(
        db,
        title=payload.get("title", ""),
        discount_pct=float(payload.get("discount_pct", 0)),
        starts_at=payload.get("starts_at", ""),
        ends_at=payload.get("ends_at", ""),
        description=payload.get("description"),
        is_active=payload.get("is_active", True),
        country_code=payload.get("country_code"),
    )
    return {
        "id": sale.id,
        "title": sale.title,
        "description": sale.description,
        "starts_at": sale.starts_at.isoformat() if sale.starts_at else None,
        "ends_at": sale.ends_at.isoformat() if sale.ends_at else None,
        "discount_pct": float(sale.discount_pct) if sale.discount_pct else 0,
        "is_active": sale.is_active,
        "country_code": sale.country_code,
        "is_deleted": sale.is_deleted,
        "created_at": sale.created_at.isoformat() if sale.created_at else None,
        "updated_at": sale.updated_at.isoformat() if sale.updated_at else None,
    }


@router.patch("/flash-sales/{sale_id}")
def update_flash_sale_route(
    sale_id: int = Path(...),
    payload: dict = Body(...),
    admin: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("promotions.promotions.write")),
):
    sale = update_flash_sale(
        db,
        sale_id=sale_id,
        title=payload.get("title"),
        description=payload.get("description"),
        discount_pct=payload.get("discount_pct"),
        starts_at=payload.get("starts_at"),
        ends_at=payload.get("ends_at"),
        is_active=payload.get("is_active"),
        country_code=payload.get("country_code"),
    )
    return {
        "id": sale.id,
        "title": sale.title,
        "description": sale.description,
        "starts_at": sale.starts_at.isoformat() if sale.starts_at else None,
        "ends_at": sale.ends_at.isoformat() if sale.ends_at else None,
        "discount_pct": float(sale.discount_pct) if sale.discount_pct else 0,
        "is_active": sale.is_active,
        "country_code": sale.country_code,
        "is_deleted": sale.is_deleted,
        "created_at": sale.created_at.isoformat() if sale.created_at else None,
        "updated_at": sale.updated_at.isoformat() if sale.updated_at else None,
    }


@router.post("/flash-sales/{sale_id}/archive", status_code=200)
def archive_flash_sale_route(
    sale_id: int = Path(...),
    admin: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("promotions.promotions.write")),
):
    result = archive_flash_sale_controller("flash_sale", sale_id, admin, db)
    return result


@router.post("/flash-sales/{sale_id}/restore", status_code=200)
def restore_flash_sale_route(
    sale_id: int = Path(...),
    admin: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("promotions.promotions.write")),
):
    result = restore_flash_sale_controller("flash_sale", sale_id, admin, db)
    return result
