"""Admin banners router — country-scoped wrapper around the public banners router."""
from fastapi import APIRouter, Depends, File, Path, UploadFile
from sqlalchemy.orm import Session

from domains.promotions.services.banners.banner_service import BannerCreate
from domains.promotions.services.banners.banner_service import BannerUpdate
from domains.promotions.services.banners.banner_service import get_banners
from domains.promotions.services.banners.banner_service import get_banners_page
from domains.catalog.services._auto_stubs import upload_banner_image
from domains.promotions.services.admin_promotion_service import create_banner as create_banner_controller
from domains.promotions.services.admin_promotion_service import delete_banner as delete_banner_controller
from domains.promotions.services.admin_promotion_service import update_banner as update_banner_controller
from infrastructure.database.database import get_db
from domains.governance.models.user import User
from domains.country.utils.country_rls import get_country_or_404
from infrastructure.utils.dependencies import require_admin
from infrastructure.utils.rls_interceptor import clear_rls_context, set_rls_context

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

