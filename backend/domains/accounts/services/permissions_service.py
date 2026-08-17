"""Auto-migrated service logic from routers/permissions.py."""
from __future__ import annotations
from __future__ import annotations
from typing import Optional
from fastapi import Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from modules.admin.routers.auth import require_admin
from rbac.routers.auth_controller import get_current_user
from infrastructure.database.database import get_db
from services.security import permission_service as svc

class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    slug: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    sort_order: int = 0

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None

class PermissionCreate(BaseModel):
    category_id: int
    name: str = Field(..., min_length=1, max_length=150)
    slug: Optional[str] = None
    description: Optional[str] = None
    scope: str = 'global'

class RolePermissionAssignBody(BaseModel):
    role_name: str = Field(..., min_length=1, max_length=80)
    permission_id: int
    country_code: Optional[str] = None

class UserPermissionOverrideBody(BaseModel):
    user_id: int
    permission_id: int
    is_granted: bool = True
    country_code: Optional[str] = None
    expires_at: Optional[str] = None
from services.security.permission_service import list_categories
from services.core.admin_categories_service import create_category
from services.core.admin_categories_service import create_category
from services.core.admin_categories_service import create_category
from services.core.admin_categories_service import create_category
from services.core.admin_categories_service import create_category
from services.core.admin_categories_service import create_category
from services.core.admin_categories_service import create_category
from services.core.admin_categories_service import create_category
from services.core.admin_categories_service import create_category
from services.core.admin_categories_service import create_category
from services.core.admin_categories_service import create_category
from services.core.admin_categories_service import create_category
from services.core.admin_categories_service import create_category
from services.core.admin_categories_service import create_category
from services.core.admin_categories_service import create_category
from services.core.admin_categories_service import create_category
from services.core.admin_categories_service import create_category
from services.core.admin_categories_service import create_category
from services.core.admin_categories_service import create_category
from services.core.admin_categories_service import create_category

def __getattr__(name):
    _LAZY = {'COUNTRY_ROLE_PERMISSION_MAP': 'services.security.effective_permissions', 'HR_PERMISSION_MAP': 'services.security.effective_permissions', 'MAKER_CHECKER_PERMISSIONS': 'services.security.effective_permissions', 'approve_permission_change': 'services.security.effective_permissions', 'check_permission': 'services.security.effective_permissions', 'get_effective_permissions': 'services.security.effective_permissions', 'invalidate_permission_cache': 'services.security.effective_permissions', 'request_permission_change': 'services.security.effective_permissions'}
    if name in _LAZY:
        import importlib
        return getattr(importlib.import_module(_LAZY[name]), name)
    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
from services.security.permission_service import list_categories  # [MIGRATION COMPAT] re-export relocated symbol (see ARCHITECTURE_MIGRATION_REPORT.md)


from services.core.admin_categories_service import update_category  # [MIGRATION COMPAT] re-export relocated symbol














from services.core.admin_categories_service import delete_category  # [MIGRATION COMPAT] re-export relocated symbol











from services.admin.admin_permissions_validation_service import list_permissions  # [MIGRATION COMPAT] re-export relocated symbol













from services.admin.admin_permissions_validation_service import create_permission  # [MIGRATION COMPAT] re-export relocated symbol














from services.admin.admin_permissions_validation_service import delete_permission  # [MIGRATION COMPAT] re-export relocated symbol
from services.admin.admin_permissions_validation_service import get_role_permissions  # [MIGRATION COMPAT] re-export relocated symbol


# === auto-wiring re-exports (migration repair) ===
from services.admin.admin_permissions_validation_service import (
    assign_permission_to_role,
    check_effective_permission,
    check_permission,
    effective_permissions,
    invalidate_cache,
    maker_checker_approve,
    maker_checker_request,
    permission_catalog,
    revoke_permission_from_role,
    set_user_permission_override
)

from services.security.permission_service import list_categories  # [MIGRATION COMPAT] re-export relocated symbol (see ARCHITECTURE_MIGRATION_REPORT.md)

