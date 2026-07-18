"""Banners router."""
from typing import Optional

from fastapi import APIRouter, Depends, File, Query, Request, UploadFile
from sqlalchemy.orm import Session

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
from db.database import get_db
from models import User
from utils.dependencies import require_admin

router = APIRouter()


def _admin_context(admin: User) -> dict:
    return {
        "id": getattr(admin, "id", None),
        "username": getattr(admin, "username", None),
        "role": getattr(admin, "role", None),
    }

@router.get("", response_model=list[dict])
def list_banners(request: Request, position: Optional[str] = Query(None), db: Session = Depends(get_db)):
    country = getattr(request.state, "country_code", None)
    return get_banners(db, banner_type=position, active_only=True, country_code=country)

@router.get("/all", response_model=dict)
def list_all_banners(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    return get_banners_page(db, active_only=False)

@router.post("", response_model=dict, status_code=201)
def create_banner(payload: BannerCreate, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    return create_banner_controller(payload, getattr(admin, "id"), _admin_context(admin), db)


@router.put("/{banner_id}", response_model=dict)
def update_banner(banner_id: int, payload: BannerUpdate, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    return update_banner_controller(banner_id, payload, _admin_context(admin), db)


@router.post("/{banner_id}/image", response_model=dict)
async def upload_image(
    banner_id: int,
    file: UploadFile = File(...),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return await upload_banner_image(banner_id, file, _admin_context(admin), db)

@router.delete("/{banner_id}")
def delete_banner(banner_id: int, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    return delete_banner_controller(banner_id, _admin_context(admin), db)

