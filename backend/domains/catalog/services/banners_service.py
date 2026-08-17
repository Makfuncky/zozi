"""Auto-migrated service logic from routers/banners.py."""
from __future__ import annotations

from typing import Optional

from fastapi import Depends, File, Query, Request, UploadFile

from sqlalchemy.orm import Session

from controllers.catalog.banner_controller import (
    BannerCreate,
    BannerUpdate,
    get_banner_by_id,
    get_banners,
    get_banners_page,
    upload_banner_image,
)

from controllers.catalog.banner_controller import (
    create_banner as create_banner_controller,
)

from controllers.catalog.banner_controller import (
    delete_banner as delete_banner_controller,
)

from controllers.catalog.banner_controller import (
    update_banner as update_banner_controller,
)

from infrastructure.database.database import get_db

from models import User

from infrastructure.utils.dependencies import require_admin
from services.admin.admin_commerce_geography_service import _admin_context


def list_banners(request: Request, position: Optional[str], db: Session):
    country = getattr(request.state, "country_code", None)
    return get_banners(db, banner_type=position, active_only=True, country_code=country)

def list_all_banners(_: User, db: Session):
    return get_banners_page(db, active_only=False)

def read_banner(banner_id: int, admin: User, db: Session):
    return get_banner_by_id(banner_id, db)

def create_banner(payload: BannerCreate, admin: User, db: Session):
    return create_banner_controller(payload, admin.id, _admin_context(admin), db)

def update_banner(banner_id: int, payload: BannerUpdate, admin: User, db: Session):
    return update_banner_controller(banner_id, payload, _admin_context(admin), db)

async def upload_image(banner_id: int, file: UploadFile, admin: User, db: Session):
    return await upload_banner_image(banner_id, file, _admin_context(admin), db)

def delete_banner(banner_id: int, admin: User, db: Session):
    return delete_banner_controller(banner_id, _admin_context(admin), db)


