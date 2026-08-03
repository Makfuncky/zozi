"""
Three-Layer Effective Permission Resolver.

Layer 1 — Global Role: Base capabilities from the user's role (admin, sub_admin, etc.)
Layer 2 — Country Role: Overrides from CountryStaffAssignment (country_head, country_finance, etc.)
Layer 3 — Hierarchy-Derived: Approval rights over subordinates via can_manage() + authority_level

Precedence: Country Role > Hierarchy > Global Role
Results cached in Redis (invalidated on role/hierarchy/assignment change).
"""
from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple

from sqlalchemy.orm import Session

from data.db import SessionLocal
from data.models import User, Employee, CountryStaffAssignment, Permission, RolePermissionAssignment, UserPermissionOverride
from utils.staff_permissions import DEFAULT_ROLE_PERMISSION_MAP, STAFF_PERMISSION_GROUPS

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════
#  HR Permission Catalog (single source of truth)
# ══════════════════════════════════════════════════════════════════

HR_PERMISSION_MAP: Dict[str, List[str]] = {
    "hr.*": ["hr.*"],
    "hr.employee.read": ["hr.employee.read"],
    "hr.employee.create": ["hr.employee.create"],
    "hr.employee.update": ["hr.employee.update"],
    "hr.employee.delete": ["hr.employee.delete"],
    "hr.leave.approve": ["hr.leave.approve"],
    "hr.attendance.manage": ["hr.attendance.manage"],
    "hr.payroll.release": ["hr.payroll.release"],
    "hr.payroll.view": ["hr.payroll.view"],
    "hr.payroll.approve": ["hr.payroll.approve"],
    "hr.onboarding.manage": ["hr.onboarding.manage"],
    "hr.offboarding.initiate": ["hr.offboarding.initiate"],
    "hr.offboarding.approve": ["hr.offboarding.approve"],
    "hr.performance.manage": ["hr.performance.manage"],
    "hr.performance.review": ["hr.performance.review"],
    "hr.disciplinary.manage": ["hr.disciplinary.manage"],
    "hr.hierarchy.manage": ["hr.hierarchy.manage"],
    "hr.reports.view": ["hr.reports.view"],
    "finance.*": ["finance.*"],
    "finance.ledger.read": ["finance.ledger.read"],
    "finance.ledger.approve": ["finance.ledger.approve"],
    "finance.payout.create": ["finance.payout.create"],
    "finance.payout.approve": ["finance.payout.approve"],
    "finance.budget.manage": ["finance.budget.manage"],
    "comms.*": ["comms.*"],
    "comms.chat.manage": ["comms.chat.manage"],
    "comms.email.manage": ["comms.email.manage"],
    "comms.channel.manage": ["comms.channel.manage"],
    "country.*": ["country.*"],
    "country.configure": ["country.configure"],
    "country.staff.assign": ["country.staff.assign"],
    "country.reports.view": ["country.reports.view"],
    "admin.*": ["admin.*"],
    "admin.users.manage": ["admin.users.manage"],
    "admin.settings.manage": ["admin.settings.manage"],
    "admin.audit.view": ["admin.audit.view"],
}

# Country role → permission set mapping
COUNTRY_ROLE_PERMISSION_MAP: Dict[str, Set[str]] = {
    "country_head": {
        "hr.*", "hr.employee.read", "hr.employee.create", "hr.employee.update",
        "hr.leave.approve", "hr.attendance.manage", "hr.payroll.view",
        "hr.payroll.approve", "hr.onboarding.manage", "hr.offboarding.initiate",
        "hr.performance.manage", "hr.disciplinary.manage", "hr.hierarchy.manage",
        "hr.reports.view",
        "finance.ledger.read", "finance.payout.create", "finance.payout.approve",
        "comms.*",
        "country.*", "country.configure", "country.staff.assign", "country.reports.view",
    },
    "country_manager": {
        "hr.employee.read", "hr.employee.update",
        "hr.leave.approve", "hr.attendance.manage", "hr.payroll.view",
        "hr.onboarding.manage", "hr.performance.manage",
        "hr.reports.view",
        "finance.ledger.read",
        "comms.chat.manage",
        "country.reports.view",
    },
    "country_finance": {
        "hr.payroll.view", "hr.payroll.release",
        "finance.*", "finance.ledger.read", "finance.ledger.approve",
        "finance.payout.create", "finance.payout.approve", "finance.budget.manage",
        "country.reports.view",
    },
    "country_moderator": {
        "hr.employee.read",
        "comms.chat.manage", "comms.channel.manage",
        "country.reports.view",
    },
    "country_hr": {
        "hr.*", "hr.employee.read", "hr.employee.create", "hr.employee.update",
        "hr.leave.approve", "hr.attendance.manage", "hr.payroll.view",
        "hr.onboarding.manage", "hr.offboarding.initiate",
        "hr.performance.manage", "hr.disciplinary.manage",
        "hr.reports.view",
    },
}

# Hierarchy-derived permissions (automatically granted via can_manage)
HIERARCHY_DERIVED_PERMISSIONS: Set[str] = {
    "hr.employee.read",
    "hr.leave.approve",
    "hr.attendance.manage",
    "hr.performance.review",
    "hr.reports.view",
    "hr.offboarding.initiate",
}

# Sensitive permissions requiring Maker-Checker workflow
MAKER_CHECKER_PERMISSIONS: Set[str] = {
    "hr.payroll.release",
    "finance.ledger.approve",
    "finance.payout.approve",
    "admin.*",
    "admin.users.manage",
    "admin.settings.manage",
    "country.staff.assign",
}


# ══════════════════════════════════════════════════════════════════
#  Redis Caching Helpers
# ══════════════════════════════════════════════════════════════════


def _get_redis():
    try:
        import redis as _redis
        from utils.config import settings
        client = _redis.from_url(settings.redis_url, socket_connect_timeout=1)
        client.ping()
        return client
    except Exception:
        return None


def _cache_key(user_id: int, country_code: str) -> str:
    return f"perms:{user_id}:{country_code}"


def _cached_effective_permissions(user_id: int, country_code: str) -> Optional[list]:
    r = _get_redis()
    if not r:
        return None
    try:
        data = r.get(_cache_key(user_id, country_code))
        if data:
            return json.loads(data)
    except Exception:
        pass
    return None


def _set_cached_permissions(user_id: int, country_code: str, permissions: list, ttl_seconds: int = 300) -> None:
    r = _get_redis()
    if not r:
        return
    try:
        r.setex(_cache_key(user_id, country_code), ttl_seconds, json.dumps(permissions))
    except Exception:
        pass


def invalidate_permission_cache(user_id: int, country_code: Optional[str] = None) -> None:
    """Invalidate cached permissions for a user."""
    r = _get_redis()
    if not r:
        return
    try:
        if country_code:
            r.delete(_cache_key(user_id, country_code))
        else:
            # Invalidate all country caches for this user — scan keys
            for key in r.scan_iter(f"perms:{user_id}:*"):
                r.delete(key)
    except Exception:
        pass


def invalidate_all_for_roles(role_names: List[str]) -> None:
    """Invalidate cache for all users with given roles (expensive, use sparingly)."""
    r = _get_redis()
    if not r:
        return
    try:
        db = SessionLocal()
        users = db.query(User).filter(User.role.in_(role_names)).all()
        for user in users:
            for key in r.scan_iter(f"perms:{user.id}:*"):
                r.delete(key)
        db.close()
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════════
#  Effective Permission Resolver (3-Layer)
# ══════════════════════════════════════════════════════════════════


def _resolve_global_role_permissions(role: str) -> Set[str]:
    """Layer 1: Get permissions from the user's global role."""
    return DEFAULT_ROLE_PERMISSION_MAP.get(role, set()).copy()


def _resolve_country_role_permissions(user_id: int, country_code: str, db: Session) -> Set[str]:
    """Layer 2: Get permissions from CountryStaffAssignment role_in_country."""
    assignment = (
        db.query(CountryStaffAssignment)
        .filter(
            CountryStaffAssignment.user_id == user_id,
            CountryStaffAssignment.country_code == country_code,
            CountryStaffAssignment.is_active == True,
        )
        .first()
    )
    if not assignment:
        return set()

    return COUNTRY_ROLE_PERMISSION_MAP.get(assignment.role_in_country, set()).copy()


def _resolve_hierarchy_permissions(employee: Employee, db: Session) -> Set[str]:
    """Layer 3: Hierarchy-derived permissions based on authority_level and subtree."""
    from services.hierarchy_service import get_all_subordinates

    permissions: Set[str] = set()

    if not employee:
        return permissions

    # Check if employee manages any subordinates
    subordinates = get_all_subordinates(db, employee.user_id)
    if subordinates:
        permissions.update(HIERARCHY_DERIVED_PERMISSIONS)

    # Higher authority levels unlock more
    auth_level = employee.authority_level or 0
    if auth_level >= 3:
        permissions.add("hr.offboarding.initiate")
        permissions.add("hr.payroll.view")
    if auth_level >= 4:
        permissions.add("hr.payroll.approve")
        permissions.add("hr.disciplinary.manage")
    if auth_level >= 5:
        permissions.add("finance.ledger.read")

    return permissions


def _resolve_user_overrides(user_id: int, db: Session) -> Tuple[Set[str], Set[str]]:
    """Resolve user-level permission overrides — returns (granted, revoked) sets."""
    overrides = (
        db.query(UserPermissionOverride)
        .filter(
            UserPermissionOverride.user_id == user_id,
            (UserPermissionOverride.expires_at.is_(None) | (UserPermissionOverride.expires_at > datetime.utcnow())),
        )
        .all()
    )
    granted: Set[str] = set()
    revoked: Set[str] = set()
    for ov in overrides:
        perm = db.query(Permission).filter(Permission.id == ov.permission_id).first()
        if not perm:
            continue
        if ov.is_granted:
            granted.add(perm.slug)
        else:
            revoked.add(perm.slug)
    return granted, revoked


def get_effective_permissions(
    user_id: int,
    country_code: str,
    db: Session,
    use_cache: bool = True,
) -> List[str]:
    """Resolve the effective permissions for a user within a country.

    Combines three layers with Country Role > Hierarchy > Global Role precedence,
    applies user-level overrides, and caches the result in Redis.
    """
    if use_cache:
        cached = _cached_effective_permissions(user_id, country_code)
        if cached is not None:
            return cached

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return []

    employee = db.query(Employee).filter(Employee.user_id == user_id).first()

    # Layer 1: Global role
    global_perms = _resolve_global_role_permissions(str(user.role or ""))

    # Layer 2: Country role (overrides global)
    country_perms = _resolve_country_role_permissions(user_id, country_code, db)

    # Layer 3: Hierarchy-derived
    hierarchy_perms = _resolve_hierarchy_permissions(employee, db) if employee else set()

    # Merge with precedence: Country > Hierarchy > Global
    effective: Set[str] = set()
    effective.update(global_perms)
    effective.update(hierarchy_perms)
    effective.update(country_perms)  # Country role takes highest precedence

    # Apply user-level overrides
    granted_overrides, revoked_overrides = _resolve_user_overrides(user_id, db)
    effective.difference_update(revoked_overrides)
    effective.update(granted_overrides)

    result = sorted(effective)

    if use_cache:
        _set_cached_permissions(user_id, country_code, result)

    return result


def check_permission(
    user_id: int,
    permission_slug: str,
    country_code: str,
    db: Session,
    use_cache: bool = True,
) -> bool:
    """Check if a user has a specific permission within a country.

    Handles wildcard permissions (e.g., 'hr.*' matches 'hr.employee.read').
    """
    effective = get_effective_permissions(user_id, country_code, db, use_cache=use_cache)

    # Direct match
    if permission_slug in effective:
        return True

    # Wildcard match: e.g., 'hr.*' matches 'hr.employee.read'
    for perm in effective:
        if perm.endswith(".*"):
            prefix = perm[:-2]
            if permission_slug.startswith(prefix):
                return True

    return False


# ══════════════════════════════════════════════════════════════════
#  Maker-Checker Workflow
# ══════════════════════════════════════════════════════════════════


PENDING_ASSIGNMENTS: Dict[str, dict] = {}  # In-memory; production would use DB


def request_permission_change(
    requester_id: int,
    target_user_id: int,
    permission_slug: str,
    action: str,
    country_code: str,
    db: Session,
) -> dict:
    """Create a pending permission change requiring a second admin's approval.

    action: 'grant' or 'revoke'
    """
    if permission_slug in MAKER_CHECKER_PERMISSIONS:
        request_id = hashlib.sha256(f"{requester_id}:{target_user_id}:{permission_slug}:{datetime.utcnow().isoformat()}".encode()).hexdigest()[:12]
        PENDING_ASSIGNMENTS[request_id] = {
            "requester_id": requester_id,
            "target_user_id": target_user_id,
            "permission_slug": permission_slug,
            "action": action,
            "country_code": country_code,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat(),
            "approved_by": None,
        }
        return {
            "request_id": request_id,
            "status": "pending_review",
            "message": f"Permission '{permission_slug}' requires a second admin's approval",
        }

    # Non-sensitive — apply immediately
    _apply_permission_change(target_user_id, permission_slug, action, country_code, requester_id, db)
    return {"status": "applied", "permission": permission_slug}


def approve_permission_change(
    approver_id: int,
    request_id: str,
    db: Session,
) -> dict:
    """Second admin approves a pending permission change."""
    request = PENDING_ASSIGNMENTS.get(request_id)
    if not request:
        return {"error": "Request not found"}
    if request["status"] != "pending":
        return {"error": "Request already processed"}
    if request["requester_id"] == approver_id:
        return {"error": "Cannot approve your own request"}

    _apply_permission_change(
        request["target_user_id"],
        request["permission_slug"],
        request["action"],
        request["country_code"],
        approver_id,
        db,
    )

    request["status"] = "approved"
    request["approved_by"] = approver_id
    return {"status": "approved", "request_id": request_id}


def _apply_permission_change(
    target_user_id: int,
    permission_slug: str,
    action: str,
    country_code: str,
    actor_id: int,
    db: Session,
) -> None:
    """Apply a permission change and log the audit trail."""
    perm = db.query(Permission).filter(Permission.slug == permission_slug).first()
    if not perm:
        raise ValueError(f"Permission '{permission_slug}' not found")

    if action == "grant":
        existing = (
            db.query(UserPermissionOverride)
            .filter(
                UserPermissionOverride.user_id == target_user_id,
                UserPermissionOverride.permission_id == perm.id,
                UserPermissionOverride.country_code == country_code,
            )
            .first()
        )
        if existing:
            existing.is_granted = True
            existing.expires_at = None
        else:
            override = UserPermissionOverride(
                user_id=target_user_id,
                permission_id=perm.id,
                country_code=country_code,
                is_granted=True,
                granted_by=actor_id,
            )
            db.add(override)
    elif action == "revoke":
        existing = (
            db.query(UserPermissionOverride)
            .filter(
                UserPermissionOverride.user_id == target_user_id,
                UserPermissionOverride.permission_id == perm.id,
                UserPermissionOverride.country_code == country_code,
            )
            .first()
        )
        if existing:
            existing.is_granted = False
        else:
            override = UserPermissionOverride(
                user_id=target_user_id,
                permission_id=perm.id,
                country_code=country_code,
                is_granted=False,
                granted_by=actor_id,
            )
            db.add(override)

    # Audit log
    audit = PermissionAuditLog(
        actor_id=actor_id,
        action=action,
        target_user_id=target_user_id,
        permission_id=perm.id,
        country_code=country_code,
        details=f"Permission '{permission_slug}' {action}ed by user {actor_id}",
    )
    db.add(audit)
    db.commit()

    # Invalidate cache
    invalidate_permission_cache(target_user_id, country_code)


# ══════════════════════════════════════════════════════════════════
#  FastAPI Dependency
# ══════════════════════════════════════════════════════════════════


def require_permission(permission_slug: str):
    """FastAPI dependency that checks a specific permission."""
    from fastapi import Depends, HTTPException
    from data.dependencies_auth import get_current_user  # lazy import — avoids circular dep
    # Re-homed to dependencies/auth.py so services stop importing the auth controller.

    def _checker(
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db),
    ):
        user_id = int(current_user.get("id", current_user.get("sub", 0)))
        country_code = current_user.get("cc", current_user.get("country_code", "OM"))

        if not check_permission(user_id, permission_slug, country_code, db):
            raise HTTPException(
                status_code=403,
                detail=f"Missing required permission: '{permission_slug}'",
            )
        return current_user

    return _checker


from data.db import get_db
from models.security.permissions import PermissionAuditLog
