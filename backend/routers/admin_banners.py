"""Admin banners router — country-scoped wrapper around the public banners router."""
from fastapi import APIRouter, Depends, HTTPException, Query, Path, File, UploadFile
from sqlalchemy.orm import Session
from data.db import get_db
from data.models import User
from utils.dependencies import require_admin
from utils.country_rls import get_country_or_404
from utils.rls_interceptor import set_rls_context, clear_rls_context
from controllers.banner_controller import (
    BannerCreate,
    BannerUpdate,
    create_banner as create_banner_controller,
    delete_banner as delete_banner_controller,
    get_banners,
    get_banners_page,
    update_banner as update_banner_controller,
    upload_banner_image,
)

router = APIRouter()


def _admin_context(admin: User) -> dict:
    return {
        "id": getattr(admin, "id", None),
        "username": getattr(admin, "username", None),
        "role": getattr(admin, "role", None),
    }


@router.get("/banners/{country_code}")
def list_banners(country_code: str = Path(..., description="ISO country code"), position: str = None, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return get_banners(db, banner_type=position, active_only=True)
    finally:
        clear_rls_context()


@router.get("/banners/{country_code}/all")
def list_all_banners(country_code: str = Path(..., description="ISO country code"), _: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return get_banners_page(db, active_only=False)
    finally:
        clear_rls_context()


@router.post("/banners/{country_code}")
def create_banner(country_code: str = Path(..., description="ISO country code"), payload: BannerCreate = None, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return create_banner_controller(payload, getattr(admin, "id"), _admin_context(admin), db)
    finally:
        clear_rls_context()


@router.put("/banners/{country_code}/{banner_id}")
def update_banner(country_code: str = Path(..., description="ISO country code"), banner_id: int = Path(...), payload: BannerUpdate = None, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return update_banner_controller(banner_id, payload, _admin_context(admin), db)
    finally:
        clear_rls_context()


@router.post("/banners/{country_code}/{banner_id}/image")
async def upload_image(country_code: str = Path(..., description="ISO country code"), banner_id: int = Path(...), file: UploadFile = File(...), admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return await upload_banner_image(banner_id, file, _admin_context(admin), db)
    finally:
        clear_rls_context()


@router.delete("/banners/{country_code}/{banner_id}")
def delete_banner(country_code: str = Path(..., description="ISO country code"), banner_id: int = Path(...), admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return delete_banner_controller(banner_id, _admin_context(admin), db)
    finally:
        clear_rls_context()

