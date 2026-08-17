"""
Permission Management Router
3-Layer Permission Matrix: Admin → Sub-Admin (Roles) → Employee (Override)
"""
from __future__ import annotations
from typing import Optional
from fastapi import Depends, HTTPException, Path, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from controllers.security.auth_controller import get_current_user
from controllers.admin.admin_controller import require_admin
from db.database import get_db
from services.security import permission_service as svc
from utils.country_rls import get_country_or_404
from services.security.effective_permissions import get_effective_permissions as resolve_effective_perms, check_permission as resolve_check_perm, request_permission_change, approve_permission_change, invalidate_permission_cache, HR_PERMISSION_MAP, COUNTRY_ROLE_PERMISSION_MAP, MAKER_CHECKER_PERMISSIONS

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
