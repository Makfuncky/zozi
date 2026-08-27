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
from domains.country.utils.country_rls import get_country_or_404
from infrastructure.database.rls_interceptor import set_rls_context, clear_rls_context

router = APIRouter(prefix="/api/v1/admin/promotions", tags=["admin", "promotions"])


@router.get("/banners/{country_code}")
def list_banners(
    country_code: str = Path(..., description="ISO country code"),
    position: str = None,
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    require_feature("promotions.banners.read")
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
):
    require_feature("promotions.banners.read")
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
):
    require_feature("promotions.banners.write")
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
):
    require_feature("promotions.banners.write")
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
):
    require_feature("promotions.banners.write")
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return delete_banner_controller(banner_id, admin, db)
    finally:
        clear_rls_context()


@router.get("/admin_promotions_routes/health")
def health(_: dict = Depends(require_admin)):
    require_feature("promotions.banners.read")
    return {"status": "ok", "router": "admin_promotions_routes", "prefix": "/api/v1/promotions"}
