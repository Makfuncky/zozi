"""Auto-migrated service logic from routers/admin_banners.py."""
from __future__ import annotations

from fastapi import Depends, File, Path, UploadFile

from sqlalchemy.orm import Session

from domains.catalog.services.banner_controller import BannerCreate
from domains.catalog.services.banner_controller import BannerUpdate
from domains.catalog.services.banner_controller import get_banners
from domains.catalog.services.banner_controller import get_banners_page
from domains.catalog.services.banner_controller import upload_banner_image

from domains.catalog.services.banner_controller import create_banner as create_banner_controller

from domains.catalog.services.banner_controller import delete_banner as delete_banner_controller

from domains.catalog.services.banner_controller import update_banner as update_banner_controller

from infrastructure.database.database import get_db

from domains.accounts.models.user import User

from domains.country.utils.country_rls import get_country_or_404

from infrastructure.utils.dependencies import require_admin

from infrastructure.utils.rls_interceptor import clear_rls_context, set_rls_context
from domains.governance.services.admin_commerce_geography_service import _admin_context









from domains.accounts.services.banners_service import list_all_banners






















from domains.accounts.services.banners_service import create_banner














from domains.accounts.services.banners_service import update_banner











from domains.accounts.services.banners_service import upload_image













from domains.accounts.services.banners_service import delete_banner

















