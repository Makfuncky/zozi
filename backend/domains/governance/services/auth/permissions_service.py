"""Permission and category management service.

Handles category CRUD and permission lifecycle by delegating to the
catalog and governance domains via their sanctioned ports (Law 3).
"""
from __future__ import annotations

from fastapi import Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional

from infrastructure.database.database import get_db
from infrastructure.utils.dependencies import get_current_user
from domains.governance.ports import (
    list_categories,
    create_permission,
    delete_permission,
    get_role_permissions,
    assign_permission_to_role,
    revoke_permission_from_role,
    set_user_permission_override,
    check_user_permission as check_permission,
)
from domains.catalog.ports import (
    create_category,
    update_category,
    delete_category,
)


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


def list_all_categories(db: Session = Depends(get_db)):
    """List all permission categories."""
    return list_categories(db)


def create_new_category(payload: CategoryCreate, db: Session = Depends(get_db)):
    """Create a new permission category."""
    return create_category(db, **payload.model_dump(exclude_unset=True))


def update_existing_category(category_id: int, payload: CategoryUpdate, db: Session = Depends(get_db)):
    """Update an existing permission category."""
    return update_category(db, category_id, **payload.model_dump(exclude_unset=True))


def delete_existing_category(category_id: int, db: Session = Depends(get_db)):
    """Delete a permission category."""
    return delete_category(db, category_id)


def list_all_permissions(db: Session = Depends(get_db)):
    """List all permissions."""
    return list_categories(db)  # governance ports expose permissions via list_categories


def create_new_permission(payload: PermissionCreate, db: Session = Depends(get_db)):
    """Create a new permission."""
    return create_permission(db, **payload.model_dump(exclude_unset=True))


def delete_existing_permission(permission_id: int, db: Session = Depends(get_db)):
    """Delete a permission."""
    return delete_permission(db, permission_id)


def assign_permission_to_user_role(payload: RolePermissionAssignBody, db: Session = Depends(get_db)):
    """Assign a permission to a role."""
    return assign_permission_to_role(
        db,
        payload.role_name,
        payload.permission_id,
        country_code=payload.country_code,
    )


def revoke_permission_from_user_role(payload: RolePermissionAssignBody, db: Session = Depends(get_db)):
    """Revoke a permission from a role."""
    return revoke_permission_from_role(
        db,
        payload.role_name,
        payload.permission_id,
        country_code=payload.country_code,
    )


def set_user_permission(payload: UserPermissionOverrideBody, db: Session = Depends(get_db)):
    """Set a user-level permission override."""
    return set_user_permission_override(
        db,
        payload.user_id,
        payload.permission_id,
        is_granted=payload.is_granted,
        country_code=payload.country_code,
        expires_at=payload.expires_at,
    )


def check_user_has_permission(user_id: int, permission_slug: str, country_code: str, db: Session) -> bool:
    """Check if a user has a specific permission."""
    return check_permission(user_id, permission_slug, country_code, db)
