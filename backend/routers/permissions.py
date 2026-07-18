"""
Permission Management Router
3-Layer Permission Matrix: Admin → Sub-Admin (Roles) → Employee (Override)
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from controllers.auth_controller import get_current_user
from controllers.admin_controller import require_admin
from db.database import get_db
from services import permission_service as svc
from utils.country_rls import get_country_or_404

router = APIRouter(tags=["permissions"])


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
    scope: str = "global"


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


@router.get("/categories")
def list_categories(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_admin(current_user)
    return svc.list_categories(db)


@router.post("/categories")
def create_category(
    body: CategoryCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_admin(current_user)
    return svc.create_category(body.model_dump(exclude_none=True), current_user.get("id"), db)


@router.put("/categories/{category_id}")
def update_category(
    category_id: int,
    body: CategoryUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_admin(current_user)
    result = svc.update_category(category_id, body.model_dump(exclude_none=True), current_user.get("id"), db)
    if not result:
        raise HTTPException(status_code=404, detail="Category not found")
    return result


@router.delete("/categories/{category_id}")
def delete_category(
    category_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_admin(current_user)
    if not svc.delete_category(category_id, current_user.get("id"), db):
        raise HTTPException(status_code=404, detail="Category not found")
    return {"message": "Category deleted"}


@router.get("/list")
def list_permissions(
    category_id: Optional[int] = Query(None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_admin(current_user)
    return svc.list_permissions(db, category_id=category_id)


@router.post("/")
def create_permission(
    body: PermissionCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_admin(current_user)
    return svc.create_permission(body.model_dump(exclude_none=True), current_user.get("id"), db)


@router.delete("/{permission_id}")
def delete_permission(
    permission_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_admin(current_user)
    if not svc.delete_permission(permission_id, current_user.get("id"), db):
        raise HTTPException(status_code=404, detail="Permission not found")
    return {"message": "Permission deactivated"}


@router.get("/roles/{role_name}")
def get_role_permissions(
    role_name: str,
    country_code: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_admin(current_user)
    return svc.get_role_permissions(role_name, country_code=country_code, db=db)


@router.post("/roles/assign")
def assign_permission_to_role(
    body: RolePermissionAssignBody,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_admin(current_user)
    result = svc.assign_permission_to_role(
        body.role_name, body.permission_id, current_user.get("id"), db, country_code=body.country_code
    )
    return {"message": "Permission assigned to role", "assignment_id": result.id}


@router.post("/roles/revoke")
def revoke_permission_from_role(
    body: RolePermissionAssignBody,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_admin(current_user)
    if not svc.revoke_permission_from_role(body.role_name, body.permission_id, current_user.get("id"), db):
        raise HTTPException(status_code=404, detail="Assignment not found")
    return {"message": "Permission revoked from role"}


@router.post("/users/override")
def set_user_permission_override(
    body: UserPermissionOverrideBody,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_admin(current_user)
    result = svc.set_user_permission_override(
        user_id=body.user_id,
        permission_id=body.permission_id,
        actor_id=current_user.get("id"),
        db=db,
        country_code=body.country_code,
        is_granted=body.is_granted,
        expires_at=body.expires_at,
    )
    return {"message": "User permission override set", "override_id": result.id}


@router.get("/check/{user_id}/{permission_slug}")
def check_permission(
    user_id: int,
    permission_slug: str,
    country_code: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_admin(current_user)
    result = svc.check_user_permission(user_id, permission_slug, db, country_code=country_code)
    return {"granted": result}

