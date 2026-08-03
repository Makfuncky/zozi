"""
Permission Management Router
3-Layer Permission Matrix: Admin → Sub-Admin (Roles) → Employee (Override)
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from data.dependencies_auth import get_current_user
from data.controllers_admin_controller import require_admin
from data.db import get_db
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


# ══════════════════════════════════════════════════════════════════
#  3-Layer Effective Permission Resolver Endpoints
# ══════════════════════════════════════════════════════════════════


from services.effective_permissions import (
    get_effective_permissions as resolve_effective_perms,
    check_permission as resolve_check_perm,
    request_permission_change,
    approve_permission_change,
    invalidate_permission_cache,
    HR_PERMISSION_MAP,
    COUNTRY_ROLE_PERMISSION_MAP,
    MAKER_CHECKER_PERMISSIONS,
)


@router.get("/effective/{user_id}")
def effective_permissions(
    user_id: int,
    country_code: str = Query(..., min_length=2, max_length=10),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the merged 3-layer effective permissions for a user in a country."""
    perms = resolve_effective_perms(user_id, country_code, db)
    return {
        "user_id": user_id,
        "country_code": country_code,
        "permissions": perms,
        "count": len(perms),
    }


@router.get("/check-effective/{user_id}/{permission_slug}")
def check_effective_permission(
    user_id: int,
    permission_slug: str,
    country_code: str = Query(..., min_length=2, max_length=10),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Check a specific permission against the effective 3-layer resolver."""
    granted = resolve_check_perm(user_id, permission_slug, country_code, db)
    return {
        "user_id": user_id,
        "permission": permission_slug,
        "country_code": country_code,
        "granted": granted,
    }


@router.get("/catalog")
def permission_catalog(
    current_user: dict = Depends(get_current_user),
):
    """Return the full HR permission catalog and country role definitions."""
    require_admin(current_user)
    return {
        "permission_catalog": HR_PERMISSION_MAP,
        "country_roles": {role: sorted(perms) for role, perms in COUNTRY_ROLE_PERMISSION_MAP.items()},
        "maker_checker_permissions": sorted(MAKER_CHECKER_PERMISSIONS),
    }


@router.post("/maker-checker/request")
def maker_checker_request(
    target_user_id: int = Query(...),
    permission_slug: str = Query(...),
    action: str = Query(..., pattern="^(grant|revoke)$"),
    country_code: str = Query(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Request a permission change (goes through Maker-Checker if sensitive)."""
    requester_id = int(current_user.get("id", 0))
    return request_permission_change(requester_id, target_user_id, permission_slug, action, country_code, db)


@router.post("/maker-checker/approve/{request_id}")
def maker_checker_approve(
    request_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Approve a pending permission change (Maker-Checker)."""
    approver_id = int(current_user.get("id", 0))
    return approve_permission_change(approver_id, request_id, db)


@router.post("/invalidate-cache/{user_id}")
def invalidate_cache(
    user_id: int,
    country_code: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    """Invalidate the Redis permission cache for a user."""
    require_admin(current_user)
    invalidate_permission_cache(user_id, country_code)
    return {"message": f"Cache invalidated for user {user_id}"}

