"""Auto-migrated service logic from routers/users.py."""
from __future__ import annotations

from fastapi import Depends, HTTPException

from sqlalchemy.orm import Session

from infrastructure.database.database import get_db

from infrastructure.database.schemas import UserAdminUpdate, UserOut, UserUpdate

from domains.accounts.models.user import User

from infrastructure.utils.dependencies import get_current_user, require_admin







from domains.governance.services.admin_identity_operations_api_service import update_profile






















from domains.governance.services.admin_identity_operations_api_service import list_users














from domains.governance.services.admin_identity_operations_api_service import get_user











from domains.governance.services.admin_identity_operations_api_service import admin_update_user















