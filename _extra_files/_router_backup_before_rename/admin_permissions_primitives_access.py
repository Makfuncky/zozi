"""Lower-layer permission primitives shared by the routers package.

Breaks the circular import between ``routers.public_permissions_access`` and
``routers.public_effective_permissions_access``. This module depends on nothing in the
``routers`` package.

It provides:
  * the canonical permission catalog maps (country-role defaults, the HR
    permission catalog, and the maker-checker sensitive-permission set),
  * a 3-layer effective-permission resolver (country defaults + role settings
    + user overrides),
  * a maker-checker request/approve flow backed by ``RolePermissionSetting``,
  * a small in-process cache that can be invalidated per user/country.
"""
from __future__ import annotations

import json
import time
from typing import Optional

from sqlalchemy.orm import Session

from data.models import RolePermissionSetting, User
from services.db_read import first
from services.permission_primitive_write_service import (
    approve_role_permission_setting,
    upsert_role_permission_setting,
)
import structlog
logger = structlog.get_logger(__name__)

# ── In-process cache (kept tiny; TTL-bounded and invalidated explicitly) ───────
_PERMISSION_CACHE: dict = {}
_CACHE_TTL_SECONDS = 300


def _cache_key(user_id: int, country_code: Optional[str]) -> tuple:
    return (int(user_id), country_code)


def invalidate_permission_cache(user_id: Optional[int] = None, country_code: Optional[str] = None, *, role: Optional[str] = None) -> None:
    """Drop cached effective-permission results.

    * ``user_id`` (optionally scoped to ``country_code``) invalidates a single
      user's entries.
    * ``role`` invalidates every cached entry for that role/country — required
      because role-permission settings are role-wide, so a change to one role
      affects all users of that role.
    """
    if user_id is not None:
        if country_code is not None:
            _PERMISSION_CACHE.pop(_cache_key(user_id, country_code), None)
        else:
            for key in list(_PERMISSION_CACHE):
                if key[0] == int(user_id):
                    _PERMISSION_CACHE.pop(key, None)
    if role is not None:
        for key, entry in list(_PERMISSION_CACHE.items()):
            if entry and entry[0] == role and (country_code is None or key[1] == country_code):
                _PERMISSION_CACHE.pop(key, None)


# ── Permission catalogs ────────────────────────────────────────────────────────
COMMON_PERMISSIONS = {
    "view_dashboard", "view_catalog", "view_orders", "edit_profile",
    "manage_cart", "view_notifications",
}

ADMIN_PERMISSIONS = COMMON_PERMISSIONS | {
    "admin_access", "manage_users", "manage_roles", "manage_permissions",
    "manage_disputes", "manage_banners", "manage_suppliers", "manage_finance",
    "manage_logistics", "view_audit_logs", "manage_country_settings",
}

SUPPLIER_PERMISSIONS = COMMON_PERMISSIONS | {
    "manage_products", "manage_orders", "manage_disputes", "view_payouts",
    "manage_badges", "manage_shipping",
}

CUSTOMER_PERMISSIONS = COMMON_PERMISSIONS | {
    "place_order", "manage_addresses", "view_invoices", "request_return",
}

COUNTRY_ROLE_PERMISSION_MAP: dict[str, dict[str, set]] = {
    "AE": {
        "admin": set(ADMIN_PERMISSIONS),
        "supplier": set(SUPPLIER_PERMISSIONS),
        "customer": set(CUSTOMER_PERMISSIONS),
        "employee": set(COMMON_PERMISSIONS) | {"hr_access", "employee_self_service"},
    },
    "SA": {
        "admin": set(ADMIN_PERMISSIONS),
        "supplier": set(SUPPLIER_PERMISSIONS),
        "customer": set(CUSTOMER_PERMISSIONS),
        "employee": set(COMMON_PERMISSIONS) | {"hr_access", "employee_self_service"},
    },
    "OM": {
        "admin": set(ADMIN_PERMISSIONS),
        "supplier": set(SUPPLIER_PERMISSIONS),
        "customer": set(CUSTOMER_PERMISSIONS),
        "employee": set(COMMON_PERMISSIONS) | {"hr_access", "employee_self_service"},
    },
}

# HR permission catalog: human-readable descriptions for the /catalog endpoint.
HR_PERMISSION_MAP: dict[str, str] = {
    "hr_access": "Access the HR control center",
    "employee_self_service": "Employee self-service (view own records)",
    "manage_employees": "Create/update employee records",
    "manage_attendance": "Manage attendance & timesheets",
    "manage_payroll": "Run and approve payroll",
    "manage_leave": "Approve leave requests",
    "manage_recruitment": "Manage hiring pipeline",
    "manage_performance": "Manage performance reviews",
    "manage_training": "Assign training modules",
    "manage_offboarding": "Process offboarding cases",
    "view_employee_pim": "View employee personally-identifiable data",
}

# Permissions that require a Maker-Checker approval step before they take effect.
MAKER_CHECKER_PERMISSIONS = {
    "manage_roles", "manage_permissions", "manage_finance", "manage_users",
    "manage_country_settings", "manage_payroll", "view_employee_pim",
}


def _role_permissions(role: str, country_code: Optional[str]) -> set:
    country_map = COUNTRY_ROLE_PERMISSION_MAP.get(country_code or "AE", {})
    return set(country_map.get(role, set()))


def _setting_permissions(role: str, country_code: Optional[str], db: Session) -> set:
    setting = first(
        db,
        RolePermissionSetting,
        [
            RolePermissionSetting.role == role,
            RolePermissionSetting.country_code == country_code,
        ],
    )
    if setting is None or not setting.permissions_json:
        return set()
    try:
        data = setting.permissions_json
        if isinstance(data, str):
            data = json.loads(data)
        return set(data or [])
    except (ValueError, TypeError) as e:
        logger.exception("_setting_permissions_failed", error=str(e))
        return set()


def get_effective_permissions(user_id: int, country_code: str, db: Session) -> list:
    """Return the merged 3-layer effective permission set for a user.

    Layers: country-role defaults -> role permission setting (DB) -> user
    permission overrides. Results are cached per (user, country) with a TTL and
    keyed by role so role-wide invalidation can drop them.
    """
    role = None
    user_overrides: set = set()
    user = first(db, User, [User.id == int(user_id)])
    if user is not None:
        role = getattr(user, "role", None)
        overrides = getattr(user, "permission_overrides", None)
        if overrides:
            try:
                user_overrides = set(overrides if isinstance(overrides, (list, set)) else json.loads(overrides))
            except (ValueError, TypeError) as e:
                logger.exception("get_effective_permissions_failed", error=str(e))
                user_overrides = set()

    if not role:
        role = "customer"

    key = _cache_key(user_id, country_code)
    cached = _PERMISSION_CACHE.get(key)
    if cached is not None:
        c_role, c_expiry, c_result = cached
        if c_role == role and time.time() < c_expiry:
            return list(c_result)

    perms = set()
    perms |= _role_permissions(role, country_code)
    perms |= _setting_permissions(role, country_code, db)
    perms |= user_overrides
    perms.discard("")  # guard against empty-string noise

    result = sorted(perms)
    _PERMISSION_CACHE[key] = (role, time.time() + _CACHE_TTL_SECONDS, result)
    return result


def _role_for_user(user_id: int, db: Session) -> str:
    user = first(db, User, [User.id == int(user_id)])
    return getattr(user, "role", "customer") if user else "customer"


def request_permission_change(
    requester_id: int,
    target_user_id: int,
    permission_slug: str,
    action: str,
    country_code: str,
    db: Session,
) -> dict:
    """Request (or directly apply) a permission change for a user's role.

    Sensitive permissions go through Maker-Checker: the change is staged on the
    ``RolePermissionSetting`` for the target user's role (pending) and must be
    approved. Non-sensitive permissions are applied immediately.
    """
    role = _role_for_user(target_user_id, db)
    requires_mc = permission_slug in MAKER_CHECKER_PERMISSIONS

    current = _setting_permissions(role, country_code, db)
    if action == "grant":
        current.add(permission_slug)
    else:
        current.discard(permission_slug)

    staged = json.dumps(sorted(current))
    if requires_mc:
        # Stage the change; it is NOT written to the active ``permissions_json``
        # until an approver promotes it via ``approve_permission_change``.
        upsert_role_permission_setting(
            db,
            role=role,
            country_code=country_code,
            permissions_json=staged,
            updated_by=requester_id,
            pending_permissions_json=staged,
            is_approved=False,
        )
        status = "pending_maker_checker"
    else:
        upsert_role_permission_setting(
            db,
            role=role,
            country_code=country_code,
            permissions_json=staged,
            updated_by=requester_id,
        )
        status = "applied"

    invalidate_permission_cache(target_user_id, country_code, role=role)
    return {
        "target_user_id": target_user_id,
        "role": role,
        "permission": permission_slug,
        "action": action,
        "country_code": country_code,
        "status": status,
    }


def approve_permission_change(approver_id: int, request_id: str, db: Session) -> dict:
    """Approve a maker-checker permission change.

    The staged effective set on the ``RolePermissionSetting`` (id == request_id)
    is already persisted; approval simply re-commits it as the live set and
    invalidates the cache. Because the sensitive set is staged on the same row,
    approval promotes it to active use.
    """
    setting = approve_role_permission_setting(db, setting_id=request_id, approver_id=approver_id)
    if setting is None:
        return {"status": "not_found", "request_id": request_id}
    invalidate_permission_cache(role=setting.role, country_code=setting.country_code)
    return {"status": "approved", "request_id": request_id, "role": setting.role}
