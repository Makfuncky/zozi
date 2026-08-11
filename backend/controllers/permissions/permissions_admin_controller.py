"""Thin orchestration controller for permission-management admin operations.

The ``routers.admin_permissions_validation`` router delegates to this controller so
it stays within the allowed circuit (routers -> controllers/schemas/auth-deps only).
Persistence and the 3-layer effective-permission resolution are owned by
``services.security.permission_service`` and ``services.security.effective_permissions`` respectively.
"""
from __future__ import annotations

from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from services.security import permission_service as svc
from services.security.effective_permissions import (
    get_effective_permissions as _resolve_effective_perms,
    check_permission as _resolve_check_perm,
    request_permission_change,
    approve_permission_change,
    invalidate_permission_cache,
    HR_PERMISSION_MAP,
    COUNTRY_ROLE_PERMISSION_MAP,
    MAKER_CHECKER_PERMISSIONS,
)
from controllers.admin.admin_controller import require_admin


def list_categories(db: Session) -> list[dict]:
    return svc.list_categories(db)


def create_category(data: dict, actor_id: int, db: Session):
    return svc.create_category(data, actor_id, db)


def update_category(category_id: int, data: dict, actor_id: int, db: Session):
    result = svc.update_category(category_id, data, actor_id, db)
    if not result:
        raise HTTPException(status_code=404, detail="Category not found")
    return result


def delete_category(category_id: int, actor_id: int, db: Session) -> dict:
    if not svc.delete_category(category_id, actor_id, db):
        raise HTTPException(status_code=404, detail="Category not found")
    return {"message": "Category deleted"}


def list_permissions(db: Session, category_id: Optional[int] = None) -> list[dict]:
    return svc.list_permissions(db, category_id=category_id)


def create_permission(data: dict, actor_id: int, db: Session):
    return svc.create_permission(data, actor_id, db)


def delete_permission(permission_id: int, actor_id: int, db: Session) -> dict:
    if not svc.delete_permission(permission_id, actor_id, db):
        raise HTTPException(status_code=404, detail="Permission not found")
    return {"message": "Permission deactivated"}


def get_role_permissions(role_name: str, country_code: Optional[str], db: Session) -> dict:
    return svc.get_role_permissions(role_name, country_code=country_code, db=db)


def assign_permission_to_role(role_name: str, permission_id: int, actor_id: int, db: Session, country_code: Optional[str] = None) -> dict:
    result = svc.assign_permission_to_role(role_name, permission_id, actor_id, db, country_code=country_code)
    return {"message": "Permission assigned to role", "assignment_id": result.id}


def revoke_permission_from_role(role_name: str, permission_id: int, actor_id: int, db: Session) -> dict:
    if not svc.revoke_permission_from_role(role_name, permission_id, actor_id, db):
        raise HTTPException(status_code=404, detail="Assignment not found")
    return {"message": "Permission revoked from role"}


def set_user_permission_override(user_id: int, permission_id: int, actor_id: int, db: Session, country_code: Optional[str] = None, is_granted: bool = True, expires_at: Optional[str] = None) -> dict:
    result = svc.set_user_permission_override(
        user_id=user_id,
        permission_id=permission_id,
        actor_id=actor_id,
        db=db,
        country_code=country_code,
        is_granted=is_granted,
        expires_at=expires_at,
    )
    return {"message": "User permission override set", "override_id": result.id}


def check_user_permission(user_id: int, permission_slug: str, db: Session, country_code: Optional[str] = None) -> dict:
    result = svc.check_user_permission(user_id, permission_slug, db, country_code=country_code)
    return {"granted": result}


def effective_permissions(user_id: int, country_code: str, db: Session) -> dict:
    perms = _resolve_effective_perms(user_id, country_code, db)
    return {
        "user_id": user_id,
        "country_code": country_code,
        "permissions": perms,
        "count": len(perms),
    }


def check_effective_permission(user_id: int, permission_slug: str, country_code: str, db: Session) -> dict:
    granted = _resolve_check_perm(user_id, permission_slug, country_code, db)
    return {
        "user_id": user_id,
        "permission": permission_slug,
        "country_code": country_code,
        "granted": granted,
    }


def permission_catalog() -> dict:
    return {
        "permission_catalog": HR_PERMISSION_MAP,
        "country_roles": {role: sorted(perms) for role, perms in COUNTRY_ROLE_PERMISSION_MAP.items()},
        "maker_checker_permissions": sorted(MAKER_CHECKER_PERMISSIONS),
    }


def maker_checker_request(requester_id: int, target_user_id: int, permission_slug: str, action: str, country_code: str, db: Session):
    return request_permission_change(requester_id, target_user_id, permission_slug, action, country_code, db)


def maker_checker_approve(approver_id: int, request_id: str, db: Session):
    return approve_permission_change(approver_id, request_id, db)


def invalidate_cache(user_id: int, country_code: Optional[str] = None) -> dict:
    invalidate_permission_cache(user_id, country_code)
    return {"message": f"Cache invalidated for user {user_id}"}
