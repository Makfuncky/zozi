from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session, selectinload

# Lazy-loaded cross-domain models (Law 3: avoid direct cross-domain model imports at module level)
_LAZY_CROSS_DOMAIN_MODELS: dict[str, tuple[str, str]] = {
    "Permission": ("domains.governance.models.permissions", "Permission"),
    "PermissionAuditLog": ("domains.governance.models.permissions", "PermissionAuditLog"),
    "PermissionCategory": ("domains.governance.models.permissions", "PermissionCategory"),
    "RolePermissionAssignment": ("domains.governance.models.permissions", "RolePermissionAssignment"),
    "UserPermissionOverride": ("domains.governance.models.permissions", "UserPermissionOverride"),
}
_IMPORTED_CROSS_DOMAIN: dict[str, object] = {}


def _get_cross_domain_model(name: str):
    """Lazily import a cross-domain model to avoid import-time coupling."""
    if name in _IMPORTED_CROSS_DOMAIN:
        return _IMPORTED_CROSS_DOMAIN[name]
    if name in _LAZY_CROSS_DOMAIN_MODELS:
        module_path, class_name = _LAZY_CROSS_DOMAIN_MODELS[name]
        import importlib
        mod = importlib.import_module(module_path)
        cls = getattr(mod, class_name)
        _IMPORTED_CROSS_DOMAIN[name] = cls
        return cls
    raise AttributeError(f"Cross-domain model {name!r} not registered")


def __getattr__(name: str):
    """Module-level lazy resolver for cross-domain models (Law 3)."""
    try:
        return _get_cross_domain_model(name)
    except AttributeError:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

from infrastructure.utils.performance_cache import cached_call

logger = logging.getLogger(__name__)

_PERMISSION_CACHE_TTL = 300  # 5 minutes with jitter
_ROLE_PERMISSIONS_CACHE_TTL = 300  # 5 minutes with jitter


def _get_permission_cache_key(user_id: int, permission_slug: str, country_code: Optional[str] = None) -> tuple[str, ...]:
    return ("check", str(user_id), permission_slug, country_code or "global")


def _get_role_permissions_cache_key(role_name: str, country_code: Optional[str] = None) -> tuple[str, ...]:
    return ("role_perms", role_name, country_code or "global")


# ── Permission Category CRUD ──────────────────────────────────────


def list_categories(db: Session) -> list[dict]:
    categories = (
        db.query(PermissionCategory)
        .options(selectinload(PermissionCategory.permissions))
        .order_by(PermissionCategory.sort_order)
        .all()
    )
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
    try:
        db.commit()
        db.refresh(category)
    except Exception as exc:
        db.rollback()
        logger.warning("Failed to create category '%s': %s", data.get("name"), exc)
        raise

    _log_audit(actor_id, "category_created", target_role=None, permission_id=None, country_code=None, details=f"Created category '{category.name}'", db=db)
    return category


def update_category(category_id: int, data: dict, actor_id: int, db: Session) -> Optional[PermissionCategory]:
    category = db.query(PermissionCategory).filter(PermissionCategory.id == category_id).first()
    if not category:
        return None
    for key in ("name", "slug", "description", "icon", "sort_order", "is_active"):
        if key in data:
            setattr(category, key, data[key])
    try:
        db.commit()
        db.refresh(category)
    except Exception as exc:
        db.rollback()
        logger.warning("Failed to update category %s: %s", category_id, exc)
        raise
    _log_audit(actor_id, "category_updated", target_role=None, permission_id=None, country_code=None, details=f"Updated category '{category.name}'", db=db)
    return category


def delete_category(category_id: int, actor_id: int, db: Session) -> bool:
    category = db.query(PermissionCategory).filter(PermissionCategory.id == category_id).first()
    if not category:
        return False
    _log_audit(actor_id, "category_deleted", target_role=None, permission_id=None, country_code=None, details=f"Deleted category '{category.name}'", db=db)
    db.delete(category)
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.warning("Failed to delete category %s: %s", category_id, exc)
        raise
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
    try:
        db.commit()
        db.refresh(permission)
    except Exception as exc:
        db.rollback()
        logger.warning("Failed to create permission '%s': %s", data.get("name"), exc)
        raise
    _log_audit(actor_id, "permission_created", target_role=None, permission_id=permission.id, country_code=None, details=f"Created permission '{permission.name}'", db=db)
    return permission


def delete_permission(permission_id: int, actor_id: int, db: Session) -> bool:
    permission = db.query(Permission).filter(Permission.id == permission_id).first()
    if not permission:
        return False
    _log_audit(actor_id, "permission_deleted", target_role=None, permission_id=permission_id, country_code=None, details=f"Deleted permission '{permission.name}'", db=db)
    permission.is_active = False
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.warning("Failed to delete permission %s: %s", permission_id, exc)
        raise
    return True


# ── Role ↔ Permission Assignments ─────────────────────────────────


def get_role_permissions(role_name: str, country_code: Optional[str] = None, db: Session = None) -> dict:
    cache_key = _get_role_permissions_cache_key(role_name, country_code)

    def _compute() -> dict:
        q = db.query(RolePermissionAssignment).filter(RolePermissionAssignment.role_name == role_name)
        if country_code:
            q = q.filter(
                (RolePermissionAssignment.country_code == country_code) |
                (RolePermissionAssignment.country_code.is_(None))
            )
        assignments = q.all()
        permission_ids = [a.permission_id for a in assignments]
        perm_map: dict[int, Permission] = {}
        if permission_ids:
            perm_map = {
                p.id: p for p in db.query(Permission).filter(
                    Permission.id.in_(permission_ids)
                ).all()
            }
        permissions = {}
        for a in assignments:
            perm = perm_map.get(a.permission_id)
            if perm:
                permissions[perm.slug] = {"granted": a.is_granted, "permission_id": perm.id, "name": perm.name}
        return permissions

    return cached_call(
        prefix="perf:permissions",
        ttl=_ROLE_PERMISSIONS_CACHE_TTL,
        key_parts=cache_key,
        compute_fn=_compute,
    )


def assign_permission_to_role(role_name: str, permission_id: int, actor_id: int, db: Session, country_code: Optional[str] = None) -> RolePermissionAssignment:
    existing = db.query(RolePermissionAssignment).filter(
        RolePermissionAssignment.role_name == role_name,
        RolePermissionAssignment.permission_id == permission_id,
    ).first()
    if existing:
        existing.is_granted = True
        existing.country_code = country_code
        existing.updated_at = datetime.now(timezone.utc)
        try:
            db.commit()
            db.refresh(existing)
        except Exception as exc:
            db.rollback()
            logger.warning("Failed to update role permission '%s': %s", role_name, exc)
            raise
        _invalidate_role_cache(role_name)
        return existing

    assignment = RolePermissionAssignment(
        role_name=role_name,
        permission_id=permission_id,
        country_code=country_code,
        granted_by=actor_id,
        is_granted=True,
    )
    db.add(assignment)
    try:
        db.commit()
        db.refresh(assignment)
    except Exception as exc:
        db.rollback()
        logger.warning("Failed to assign permission to role '%s': %s", role_name, exc)
        raise
    _invalidate_role_cache(role_name)
    return assignment


def revoke_permission_from_role(role_name: str, permission_id: int, actor_id: int, db: Session) -> bool:
    existing = db.query(RolePermissionAssignment).filter(
        RolePermissionAssignment.role_name == role_name,
        RolePermissionAssignment.permission_id == permission_id,
    ).first()
    if not existing:
        return False
    existing.is_granted = False
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.warning("Failed to revoke permission from role '%s': %s", role_name, exc)
        raise
    _log_audit(actor_id, "role_permission_revoked", target_role=role_name, permission_id=permission_id, country_code=None, details=f"Revoked permission id={permission_id} from role '{role_name}'", db=db)
    _invalidate_role_cache(role_name)
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
        try:
            db.commit()
            db.refresh(existing)
        except Exception as exc:
            db.rollback()
            logger.warning("Failed to update user permission override for user %s: %s", user_id, exc)
            raise
        _invalidate_user_cache(user_id)
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
    try:
        db.commit()
        db.refresh(override)
    except Exception as exc:
        db.rollback()
        logger.warning("Failed to set user permission override for user %s: %s", user_id, exc)
        raise
    _invalidate_user_cache(user_id)
    return override


def _invalidate_role_cache(role_name: str) -> None:
    """Invalidate cached role permissions."""
    try:
        from infrastructure.utils.performance_cache import invalidate_role_permissions_cache as _invalidate
        _invalidate(role_name)
    except Exception as exc:
        logger.warning("Failed to invalidate role cache for %s: %s", role_name, exc)


def _invalidate_user_cache(user_id: int) -> None:
    """Invalidate cached user permission checks."""
    try:
        from infrastructure.utils.performance_cache import invalidate_user_permissions_cache as _invalidate
        _invalidate(user_id)
    except Exception as exc:
        logger.warning("Failed to invalidate user cache for %s: %s", user_id, exc)


# ── Permission Check ──────────────────────────────────────────────


def check_user_permission(user_id: int, permission_slug: str, db: Session, country_code: Optional[str] = None, user_role: Optional[str] = None) -> bool:
    cache_key = _get_permission_cache_key(user_id, permission_slug, country_code)

    def _compute() -> bool:
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

    return cached_call(
        prefix="perf:permissions",
        ttl=_PERMISSION_CACHE_TTL,
        key_parts=cache_key,
        compute_fn=_compute,
    )


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
    try:
        db.add(log)
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.warning("Failed to log audit: %s", exc)
        raise



# === MERGED FROM rbac_service.py ===
"""Role-Based Access Control service with delegation workflows."""




from datetime import datetime

from typing import Optional, List, Dict, Any



from sqlalchemy.orm import Session



from domains.governance.models.user import User
# TODO: CountryStaffAssignment not found in country.ports
# from domains.country.ports import CountryStaffAssignment
from domains.hr.ports import Employee
from rbac.dependencies import _ROLE_FEATURES

DEFAULT_ROLE_PERMISSION_MAP: dict = {role: set(features) for role, features in _ROLE_FEATURES.items()}




class RBACService:

    """Service for role-based access control and delegation workflows."""



    DEFAULT_ROLES = {

        role: {"permissions": sorted(permissions)}

        for role, permissions in DEFAULT_ROLE_PERMISSION_MAP.items()

    }

    

    def __init__(self, db: Session):

        self.db = db

    

    def get_user_role(self, user_id: int) -> str:

        """Get user's role."""

        user = self.db.query(User).filter(User.id == user_id).first()

        return user.role if user else "customer"

    

    def get_user_permissions(self, user_id: int) -> List[str]:

        """Get user's permissions based on role."""

        role = self.get_user_role(user_id)

        role_def = self.DEFAULT_ROLES.get(role, {"permissions": []})

        return list(role_def.get("permissions", []))

    

    def get_user_country_scope(self, user_id: int) -> List[str]:

        """Get countries user has access to."""

        user = self.db.query(User).filter(User.id == user_id).first()

        if not user:

            return []

        

        role = str(user.role or "").lower()

        if role == "admin":

            return ["ALL"]

        

        staff_codes = user.staff_country_codes or []

        return [str(c).strip().upper() for c in staff_codes]

    

    def check_permission(self, user_id: int, permission: str, country_code: str = None) -> bool:

        """Check if user has a specific permission for a country."""

        permissions = self.get_user_permissions(user_id)

        if permission not in permissions:

            return False

        

        if country_code:

            scope = self.get_user_country_scope(user_id)

            if "ALL" not in scope and country_code.upper() not in scope:

                return False

        

        return True

    

    def delegate_permission(

        self,

        delegator_id: int,

        delegatee_id: int,

        permission: str,

        country_code: str,

        valid_until: datetime,

        notes: str = None,

    ) -> bool:

        """Delegate a permission to another user (e.g., manager approval)."""

        if not self.check_permission(delegator_id, "approve"):

            return False

        

        if not self.check_permission(delegator_id, "write", country_code):

            return False

        

        return True

    

    def request_leave_approval(

        self,

        employee_id: int,

        leave_request_id: int,

        approver_id: int,

    ) -> bool:

        """Request leave approval through delegation workflow."""

        if not self.check_permission(approver_id, "approve"):

            return False

        

        employee = (

            self.db.query(Employee)

            .filter(Employee.id == employee_id)

            .first()

        )

        if not employee:

            return False

        

        if employee.user_id != approver_id:

            if not self.check_permission(approver_id, "manage_operations", employee.country_code):

                return False

        

        return True

    

    def get_delegation_chain(self, user_id: int) -> List[Dict[str, Any]]:

        """Get the delegation chain for a user."""

        user = self.db.query(User).filter(User.id == user_id).first()

        if not user:

            return []



        role = str(user.role or "").lower()

        if role == "admin":

            return [{"type": "admin", "id": user.id}]



        employee = (

            self.db.query(Employee)

            .filter(Employee.user_id == user_id)

            .first()

        )

        if not employee:

            return []



        chain = []

        if employee.hiring_manager_id:

            chain.append({"type": "hiring_manager", "id": employee.hiring_manager_id})

        if employee.reporting_manager_id:

            chain.append({"type": "reports_to", "id": employee.reporting_manager_id})



        return chain



    def can_approve_resource(

        self,

        user_id: int,

        resource_type: str,

        amount: Optional[float] = None,

    ) -> Dict[str, Any]:

        """Check if user can approve a resource using the approval matrix."""

        from domains.governance.core.approval_matrix_service import can_approve as _can_approve

        return _can_approve(self.db, user_id, resource_type, amount=amount)



    def resolve_resource_approvers(

        self,

        resource_type: str,

        org_unit_id: Optional[int] = None,

    ) -> List[Dict[str, Any]]:

        """Find all users who can approve a given resource type."""

        from domains.governance.core.approval_matrix_service import resolve_approvers as _resolve

        return _resolve(self.db, resource_type, org_unit_id=org_unit_id)



    def get_resource_approval_chain(

        self,

        user_id: int,

        resource_type: str,

    ) -> List[Dict[str, Any]]:

        """Get the user's chain of approvers for a resource type."""

        from domains.governance.core.approval_matrix_service import get_approval_chain as _chain

        return _chain(self.db, user_id, resource_type)





def create_rbac_service(db: Session) -> RBACService:

    return RBACService(db)



