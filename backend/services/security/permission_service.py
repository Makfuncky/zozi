

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from models.security.permissions import (
    Permission,
    PermissionAuditLog,
    PermissionCategory,
    RolePermissionAssignment,
    UserPermissionOverride,
)

logger = logging.getLogger(__name__)


# ── Permission Category CRUD ──────────────────────────────────────


def list_categories(db: Session) -> list[dict]:
    categories = db.query(PermissionCategory).order_by(PermissionCategory.sort_order).all()
    return [
        {
            "id": c.id,
            "name": c.name,
            "slug": c.slug,
            "description": c.description,
            "icon": c.icon,
            "sort_order": c.sort_order,
            "permissions_count": len(c.permissions),
            "is_active": c.is_active,
            "permissions": [
                {
                    "id": p.id,
                    "name": p.name,
                    "slug": p.slug,
                    "description": p.description,
                    "scope": p.scope,
                    "is_active": p.is_active,
                }
                for p in c.permissions
            ],
        }
        for c in categories
    ]


def create_category(data: dict, actor_id: int, db: Session) -> PermissionCategory:
    category = PermissionCategory(
        name=data["name"],
        slug=data.get("slug", data["name"].lower().replace(" ", "_")),
        description=data.get("description"),
        icon=data.get("icon"),
        sort_order=data.get("sort_order", 0),
        is_active=True,
    )
    db.add(category)
    db.commit()
    db.refresh(category)

    _log_audit(actor_id, "category_created", target_role=None, permission_id=None, country_code=None, details=f"Created category '{category.name}'", db=db)
    return category


def update_category(category_id: int, data: dict, actor_id: int, db: Session) -> Optional[PermissionCategory]:
    category = db.query(PermissionCategory).filter(PermissionCategory.id == category_id).first()
    if not category:
        return None
    for key in ("name", "slug", "description", "icon", "sort_order", "is_active"):
        if key in data:
            setattr(category, key, data[key])
    db.commit()
    db.refresh(category)
    _log_audit(actor_id, "category_updated", target_role=None, permission_id=None, country_code=None, details=f"Category modified: '{category.name}'", db=db)
    return category


def delete_category(category_id: int, actor_id: int, db: Session) -> bool:
    category = db.query(PermissionCategory).filter(PermissionCategory.id == category_id).first()
    if not category:
        return False
    _log_audit(actor_id, "category_deleted", target_role=None, permission_id=None, country_code=None, details=f"Category removed: '{category.name}'", db=db)
    db.delete(category)
    db.commit()
    return True


# ── Permission CRUD ───────────────────────────────────────────────


def list_permissions(db: Session, category_id: Optional[int] = None) -> list[dict]:
    q = db.query(Permission)
    if category_id:
        q = q.filter(Permission.category_id == category_id)
    permissions = q.order_by(Permission.id).all()
    return [
        {
            "id": p.id,
            "category_id": p.category_id,
            "name": p.name,
            "slug": p.slug,
            "description": p.description,
            "scope": p.scope,
            "is_active": p.is_active,
        }
        for p in permissions
    ]


def create_permission(data: dict, actor_id: int, db: Session) -> Permission:
    permission = Permission(
        category_id=data["category_id"],
        name=data["name"],
        slug=data.get("slug", data["name"].lower().replace(" ", "_")),
        description=data.get("description"),
        scope=data.get("scope", "global"),
        is_active=True,
    )
    db.add(permission)
    db.commit()
    db.refresh(permission)
    _log_audit(actor_id, "permission_created", target_role=None, permission_id=permission.id, country_code=None, details=f"Created permission '{permission.name}'", db=db)
    return permission


def delete_permission(permission_id: int, actor_id: int, db: Session) -> bool:
    permission = db.query(Permission).filter(Permission.id == permission_id).first()
    if not permission:
        return False
    _log_audit(actor_id, "permission_deleted", target_role=None, permission_id=permission_id, country_code=None, details=f"Permission '{permission.name}' removed", db=db)
    permission.is_active = False
    db.commit()
    return True


# ── Role ↔ Permission Assignments ─────────────────────────────────


def get_role_permissions(role_name: str, country_code: Optional[str] = None, db: Session = None) -> dict:
    q = db.query(RolePermissionAssignment).filter(RolePermissionAssignment.role_name == role_name)
    if country_code:
        q = q.filter(
            (RolePermissionAssignment.country_code == country_code) |
            (RolePermissionAssignment.country_code.is_(None))
        )
    assignments = q.all()
    permissions = {}
    for a in assignments:
        perm = db.query(Permission).filter(Permission.id == a.permission_id).first()
        if perm:
            permissions[perm.slug] = {"granted": a.is_granted, "permission_id": perm.id, "name": perm.name}
    return permissions


def assign_permission_to_role(role_name: str, permission_id: int, actor_id: int, db: Session, country_code: Optional[str] = None) -> RolePermissionAssignment:
    existing = db.query(RolePermissionAssignment).filter(
        RolePermissionAssignment.role_name == role_name,
        RolePermissionAssignment.permission_id == permission_id,
    ).first()
    if existing:
        existing.is_granted = True
        existing.country_code = country_code
        existing.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(existing)
        return existing

    assignment = RolePermissionAssignment(
        role_name=role_name,
        permission_id=permission_id,
        country_code=country_code,
        granted_by=actor_id,
        is_granted=True,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


def revoke_permission_from_role(role_name: str, permission_id: int, actor_id: int, db: Session) -> bool:
    existing = db.query(RolePermissionAssignment).filter(
        RolePermissionAssignment.role_name == role_name,
        RolePermissionAssignment.permission_id == permission_id,
    ).first()
    if not existing:
        return False
    existing.is_granted = False
    db.commit()
    _log_audit(actor_id, "role_permission_revoked", target_role=role_name, permission_id=permission_id, country_code=None, details=f"Revoked permission id={permission_id} from role '{role_name}'", db=db)
    return True


# ── User Permission Overrides ─────────────────────────────────────


def set_user_permission_override(user_id: int, permission_id: int, actor_id: int, db: Session, country_code: Optional[str] = None, is_granted: bool = True, expires_at: Optional[datetime] = None) -> UserPermissionOverride:
    existing = db.query(UserPermissionOverride).filter(
        UserPermissionOverride.user_id == user_id,
        UserPermissionOverride.permission_id == permission_id,
    ).first()
    if existing:
        existing.is_granted = is_granted
        existing.country_code = country_code
        existing.granted_by = actor_id
        existing.expires_at = expires_at
        db.commit()
        db.refresh(existing)
        return existing

    override = UserPermissionOverride(
        user_id=user_id,
        permission_id=permission_id,
        country_code=country_code,
        is_granted=is_granted,
        granted_by=actor_id,
        expires_at=expires_at,
    )
    db.add(override)
    db.commit()
    db.refresh(override)
    return override


# ── Permission Check ──────────────────────────────────────────────


def check_user_permission(user_id: int, permission_slug: str, db: Session, country_code: Optional[str] = None, user_role: Optional[str] = None) -> bool:
    permission = db.query(Permission).filter(Permission.slug == permission_slug, Permission.is_active == True).first()
    if not permission:
        logger.warning(f"Permission slug '{permission_slug}' not found")
        return False

    user_override = db.query(UserPermissionOverride).filter(
        UserPermissionOverride.user_id == user_id,
        UserPermissionOverride.permission_id == permission.id,
        (
            (UserPermissionOverride.expires_at.is_(None)) |
            (UserPermissionOverride.expires_at > datetime.now(timezone.utc))
        ),
    ).first()
    if user_override:
        return user_override.is_granted

    if user_role:
        assignments = db.query(RolePermissionAssignment).filter(
            RolePermissionAssignment.role_name == user_role,
            RolePermissionAssignment.permission_id == permission.id,
            RolePermissionAssignment.is_granted == True,
        ).all()
        for a in assignments:
            if a.country_code is None or (country_code and a.country_code == country_code):
                return True

    return False


# ── Helpers ───────────────────────────────────────────────────────


def _log_audit(actor_id: int, action: str, target_user_id: Optional[int] = None, target_role: Optional[str] = None, permission_id: Optional[int] = None, country_code: Optional[str] = None, details: Optional[str] = None, db: Session = None):
    log = PermissionAuditLog(
        actor_id=actor_id,
        action=action,
        target_user_id=target_user_id,
        target_role=target_role,
        permission_id=permission_id,
        country_code=country_code,
        details=details,
    )
    db.add(log)
    db.commit()

