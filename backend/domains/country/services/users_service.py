"""Auto-migrated service logic from routers/users.py."""
from __future__ import annotations

from fastapi import Depends, HTTPException

from sqlalchemy.orm import Session

from infrastructure.database.database import get_db

from infrastructure.database.schemas import UserAdminUpdate, UserOut, UserUpdate

from _legacy.models import User

from infrastructure.utils.dependencies import get_current_user, require_admin






from services.users.identity_service import get_profile  # [MIGRATION COMPAT] re-export relocated symbol (see ARCHITECTURE_MIGRATION_REPORT.md)

from services.admin.admin_identity_operations_api_service import update_profile  # [MIGRATION COMPAT] re-export relocated symbol






















from services.admin.admin_identity_operations_api_service import list_users  # [MIGRATION COMPAT] re-export relocated symbol














from services.admin.admin_identity_operations_api_service import get_user  # [MIGRATION COMPAT] re-export relocated symbol











from services.admin.admin_identity_operations_api_service import admin_update_user  # [MIGRATION COMPAT] re-export relocated symbol













from services.users.identity_service import get_profile  # [MIGRATION COMPAT] re-export relocated symbol (see ARCHITECTURE_MIGRATION_REPORT.md)


