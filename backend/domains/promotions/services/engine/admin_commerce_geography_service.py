"""Auto-migrated service logic from routers/admin_commerce_geography.py."""
from __future__ import annotations

from fastapi import Depends, HTTPException, Query, Path, File, UploadFile

from sqlalchemy.orm import Session

from infrastructure.database.database import get_db

from domains.accounts.models.user import User

from infrastructure.utils.dependencies import require_admin

from domains.country.utils.country_rls import get_country_or_404

from infrastructure.database.rls_interceptor import set_rls_context, clear_rls_context

from domains.catalog.ports import BannerCreate
from domains.catalog.ports import BannerUpdate
from domains.catalog.ports import create_banner
from domains.catalog.ports import delete_banner
from domains.catalog.ports import get_banners
from domains.catalog.ports import get_banners_page
from domains.catalog.ports import update_banner
from domains.catalog.ports import upload_banner_image

def _admin_context(admin: User) -> dict:
    return {
        "id": getattr(admin, "id", None),
        "username": getattr(admin, "username", None),
        "role": getattr(admin, "role", None),
    }

def list_banners(country_code: str, position: str, _: User, db: Session):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return get_banners(db, banner_type=position, active_only=True)
    finally:
        clear_rls_context()

def list_all_banners(country_code: str, _: User, db: Session):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return get_banners_page(db, active_only=False)
    finally:
        clear_rls_context()

def create_banner(country_code: str, payload: BannerCreate, admin: User, db: Session):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return create_banner_controller(payload, getattr(admin, "id"), _admin_context(admin), db)
    finally:
        clear_rls_context()

def update_banner(country_code: str, banner_id: int, payload: BannerUpdate, admin: User, db: Session):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return update_banner_controller(banner_id, payload, _admin_context(admin), db)
    finally:
        clear_rls_context()

async def upload_image(country_code: str, banner_id: int, file: UploadFile, admin: User, db: Session):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return await upload_banner_image(banner_id, file, _admin_context(admin), db)
    finally:
        clear_rls_context()

def delete_banner(country_code: str, banner_id: int, admin: User, db: Session):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return delete_banner_controller(banner_id, _admin_context(admin), db)
    finally:
        clear_rls_context()


