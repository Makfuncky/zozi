"""
Permission Management Router
3-Layer Permission Matrix: Admin → Sub-Admin (Roles) → Employee (Override)
"""
from __future__ import annotations
from typing import Optional
from fastapi import Depends, HTTPException, Path, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from rbac import get_current_user
from infrastructure.utils.dependencies import require_admin
from infrastructure.database.database import get_db
from infrastructure.database import permission_service as svc
from domains.country.utils.country_rls import get_country_or_404
from domains.governance.services.effective_permissions import get_effective_permissions as resolve_effective_perms
from domains.governance.services.effective_permissions import check_permission as resolve_check_perm
from domains.governance.services.effective_permissions import request_permission_change
from domains.governance.services.effective_permissions import approve_permission_change
from domains.governance.services.effective_permissions import invalidate_permission_cache
from domains.governance.services.effective_permissions import HR_PERMISSION_MAP
from domains.governance.services.effective_permissions import COUNTRY_ROLE_PERMISSION_MAP
from domains.governance.services.effective_permissions import MAKER_CHECKER_PERMISSIONS

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
