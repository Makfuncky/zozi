"""Auto-migrated service logic from routers/admin_banners.py."""
from __future__ import annotations

from fastapi import Depends, File, Path, UploadFile

from sqlalchemy.orm import Session

from controllers.catalog.banner_controller import (
    BannerCreate,
    BannerUpdate,
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

from infrastructure.utils.country_rls import get_country_or_404

from infrastructure.utils.dependencies import require_admin

from infrastructure.utils.rls_interceptor import clear_rls_context, set_rls_context
from services.admin.admin_commerce_geography_service import _admin_context








from services.core.banners_service import list_banners  # [MIGRATION COMPAT] re-export relocated symbol (see ARCHITECTURE_MIGRATION_REPORT.md)

from services.core.banners_service import list_all_banners  # [MIGRATION COMPAT] re-export relocated symbol






















from services.core.banners_service import create_banner  # [MIGRATION COMPAT] re-export relocated symbol














from services.core.banners_service import update_banner  # [MIGRATION COMPAT] re-export relocated symbol











from services.core.banners_service import upload_image  # [MIGRATION COMPAT] re-export relocated symbol













from services.core.banners_service import delete_banner  # [MIGRATION COMPAT] re-export relocated symbol















from services.core.banners_service import list_banners  # [MIGRATION COMPAT] re-export relocated symbol (see ARCHITECTURE_MIGRATION_REPORT.md)


