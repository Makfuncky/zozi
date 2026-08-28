"""rbac/dependencies.py - FastAPI gates.

require_feature(...) / require_module(...) are dependency factories used by module
routers. They resolve the current user from the request context and check against
the effective feature set from rbac/resolution.py and the catalog from rbac/catalog.py.
"""
from contextvars import ContextVar

from fastapi import Depends, HTTPException, Request, status

from rbac.catalog import FEATURE_CATALOG
from rbac.resolution import effective_features
from infrastructure.security.dependencies import get_current_user  # noqa: F401

_current_user_ctx: ContextVar = ContextVar("_current_user_ctx", default=None)


def _get_current_user():
    """Retrieve the current user from the request context or FastAPI dependency."""
    user = _current_user_ctx.get()
    if user is not None:
        return user
    return None


def set_current_user(user):
    """Set the current user in the context variable. Called by auth dependencies."""
    _current_user_ctx.set(user)


def _resolve_effective_features(user) -> set:
    """Resolve the effective feature set for a user based on role and overrides."""
    if user is None:
        return set()
    if isinstance(user, dict):
        role = user.get("role", None) or ""
        user_overrides = user.get("feature_overrides", []) or []
    else:
        role = getattr(user, "role", None) or ""
        user_overrides = getattr(user, "feature_overrides", []) or []
    role_features = _ROLE_FEATURES.get(role, [])
    return effective_features(
        role_features=role_features,
        db_grants=[],
        overrides=user_overrides,
        catalog=FEATURE_CATALOG,
    )


# Role-to-feature mapping: defines which features each role gets by default.
# Wildcards (e.g. "catalog:*") are expanded against the catalog.
_ROLE_FEATURES: dict = {
    "super_admin": ["*"],
    "admin": ["*"],
    "employee": [
        "analytics.read", "hr.read", "hr.write",
        "governance.read", "governance.write",
        "audit.read", "security.read",
    ],
    "staff": [
        "analytics.read", "hr.read",
        "governance.read", "audit.read",
    ],
    "supplier": [
        "catalog.list", "catalog.read", "catalog.write", "catalog.delete",
        "orders.list", "orders.read", "orders.write",
        "finance.commission.read", "finance.commission.write",
        "finance.ledger.read", "finance.payout.read", "finance.payout.write",
        "finance.bank.read", "finance.bank.write",
        "suppliers.onboarding.read", "suppliers.onboarding.write",
        "suppliers.documents.read", "suppliers.documents.write",
        "suppliers.health.read", "suppliers.profile.read", "suppliers.profile.write",
    ],
    "logistics_partner": [
        "logistics.read", "logistics.write",
        "orders.read", "orders.list",
    ],
    "customer": [
        "catalog.read", "orders.read", "orders.list",
        "customers.profile.read", "customers.profile.write",
    ],
}

# Role-to-module mapping: defines which modules each role can access.
_ROLE_MODULES: dict = {
    "super_admin": ["*"],
    "admin": ["*"],
    "employee": ["analytics", "hr", "governance", "audit", "security"],
    "staff": ["analytics", "hr", "governance", "audit"],
    "supplier": [
        "catalog", "orders", "finance", "suppliers", "analytics",
    ],
    "logistics_partner": ["logistics", "orders"],
    "customer": ["catalog", "orders", "customers"],
}


def require_feature(feature: str):
    """Check if the current user has the requested feature.

    Can be used as a FastAPI dependency (``Depends(require_feature("x"))``) or
    called directly in a route handler (``require_feature("x")``).
    Raises HTTPException(403) if the feature is not granted.
    """
    def _check(user=Depends(_get_current_user)) -> None:
        effective = _resolve_effective_features(user)
        if feature not in effective:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: feature '{feature}' is not granted",
            )

    # Support direct call pattern: require_feature("x") inside route handlers.
    # When called directly (not via Depends), check the context variable.
    user = _get_current_user()
    if user is not None:
        effective = _resolve_effective_features(user)
        if feature not in effective:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: feature '{feature}' is not granted",
            )
        return None

    return _check


def require_module(module: str):
    """Check if the current user has access to the requested module.

    Can be used as a FastAPI dependency (``Depends(require_module("x"))``) or
    called directly in a route handler (``require_module("x")``).
    Raises HTTPException(403) if the module is not accessible.
    """
    def _check(user=Depends(_get_current_user)) -> None:
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: not authenticated",
            )
        role = getattr(user, "role", None) or ""
        allowed_modules = _ROLE_MODULES.get(role, [])
        if "*" not in allowed_modules and module not in allowed_modules:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: module '{module}' is not accessible",
            )

    # Support direct call pattern: require_module("x") inside route handlers.
    user = _get_current_user()
    if user is not None:
        role = getattr(user, "role", None) or ""
        allowed_modules = _ROLE_MODULES.get(role, [])
        if "*" not in allowed_modules and module not in allowed_modules:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: module '{module}' is not accessible",
            )
        return None

    return _check


def require_roles(*roles: str):
    """FastAPI dependency factory that enforces role-based access.

    Can be used as ``Depends(require_roles("admin", "superadmin"))``.
    Works whether the current user is a JWT dict or an ORM User instance.
    """
    def _checker(user=Depends(_get_current_user)):
        role = None
        if isinstance(user, dict):
            role = user.get("role")
        else:
            role = getattr(user, "role", None)
        if role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: requires one of roles {roles}",
            )
        return user
    return _checker


def require_admin(user=None) -> None:
    """Enforce that the current user has an admin-level role.

    Works whether the current user is a JWT dict or an ORM User instance.
    Raises HTTPException(403) if the user is not an admin or super_admin.
    """
    if user is None:
        user = _get_current_user()
    role = None
    if isinstance(user, dict):
        role = user.get("role")
    else:
        role = getattr(user, "role", None)
    if role not in ("admin", "super_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: admin access required",
        )
