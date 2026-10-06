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
from infrastructure.security.dependencies import get_current_user_optional

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


# Features granted to unauthenticated (public) users
_PUBLIC_FEATURES: set = {
    "catalog.list",
    "catalog.read",
}


def _resolve_effective_features(user) -> set:
    """Resolve the effective feature set for a user based on role and overrides."""
    if user is None:
        return set(_PUBLIC_FEATURES)
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
        "analytics.read", "hr.read", "audit.read", "security.read",
        # Real hr atoms ("hr.write" was never an atom).
        "hr.attendance.read", "hr.attendance.manage",
        "hr.leave.read", "hr.leave.create", "hr.leave.manage",
        "hr.performance.read", "hr.performance.manage",
        "hr.payroll.read", "hr.payslip.read",
        "hr.profile.read", "hr.profile.update",
        "hr.training.read", "hr.org.read",
        "hr.department.read", "hr.employee.read",
        # Real governance atoms.
        "governance.access.read", "governance.permissions.read",
    ],
    "staff": [
        "analytics.read", "hr.read",
        "governance.access.read", "audit.read",
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
        # Real logistics atoms. "logistics.read"/"logistics.write" never existed,
        # so every shipment/scan call returned 403
        # "feature 'logistics.shipping.tracking' is not granted".
        "logistics.shipping.tracking", "logistics.shipping.manage",
        "logistics.delivery.estimates", "logistics.fulfillment.manage",
        "logistics.profile.read", "logistics.profile.write",
        "logistics.sla.manage",
        "orders.read", "orders.list",
    ],
"customer": [
            "catalog.list", "catalog.read", "orders.read", "orders.list",
            # Real customer atoms ("customers.profile.read"/"write" never existed).
            "customers.profile.manage",
            "customers.cart.manage", "customers.wishlist.manage",
            "customers.address.manage", "customers.returns.request",
            "customers.reviews.write", "customers.health.view",
            "orders.create",
        ],
    "sub_admin": [
        "accounts.user.read", "accounts.user.list", "accounts.user.update",
        "accounts.user.export", "accounts.role.assign", "accounts.role.revoke",
        "accounts.permissions.manage", "accounts.system_health.read",
        "orders.manage", "orders.read", "orders.list",
        "catalog.list", "catalog.read",
        "audit.read",
        "analytics.read",
        "governance.access.read", "governance.permissions.read", "security.read",
    ],
    "moderator": [
        "catalog.list", "catalog.read", "catalog.write", "catalog.delete",
        "catalog.product.create", "catalog.category.manage",
        "orders.list", "orders.read",
        "accounts.user.read", "accounts.user.list",
        "governance.moderation",
        "audit.read",
        "analytics.read", "security.read",
    ],
    "finance_officer": [
        "finance.ledger.read", "finance.ledger.write", "finance.ledger.post",
        "finance.ledger.reverse",
        "finance.reporting.read", "finance.reporting.generate",
        "finance.payout.read", "finance.payout.write", "finance.payout.create",
        "finance.payout.approve", "finance.payout.dispatch",
        "finance.commission.read", "finance.commission.write",
        "finance.commission.manage",
        "finance.bank.read", "finance.bank.write", "finance.bank.reconcile",
        "finance.invoice.read", "finance.invoice.create",
        "finance.audit.read",
        "finance.subledger.read", "finance.erp.read", "finance.erp.manage",
        "finance.treasury.read",
        "finance.period.close", "finance.period.manage",
        "finance.automation.read", "finance.automation.manage",
        "finance.credit.read", "finance.credit.manage",
        "finance.invoices.read", "finance.invoices.manage",
        "orders.list", "orders.read", "audit.read", "analytics.read",
    ],
    "country_manager": [
        "country.configure", "country.staff.assign", "country.reports.view",
        "country.tax.manage", "country.communications.send",
        "country.versioning.approve", "country.payouts.manage",
        "country.localization.manage", "country.cross_border.view",
        "country.cross_border.read", "country.cross_border.manage",
        "country.rls.configure", "country.config.read", "country.config.write",
        "country.read", "country.currency.configure", "country.tax.configure",
        "catalog.list", "catalog.read",
        "orders.list", "orders.read",
        "suppliers.onboarding.read", "suppliers.onboarding.write",
        "finance.commission.read", "finance.payout.read",
        "analytics.read", "audit.read", "customers.profile.manage",
    ],
    "auditor": [
        "audit.read", "audit.logs.read", "audit.logs.export",
        "audit.compliance.read", "audit.compliance.manage",
        "audit.config.read", "audit.config.manage",
        "audit.anomalies.read", "audit.anomalies.manage",
        "audit.command_center.read", "audit.command_center.configure",
        "accounts.audit.read", "accounts.command_center.read",
        "accounts.system_health.read",
        "finance.audit.read",
        "governance.audit.read", "governance.compliance.read",
        "governance.access.read",
        "security.read", "security.events.read",
        "analytics.read", "analytics.reports.read", "analytics.reports.export",
        "orders.list", "orders.read",
        "catalog.list", "catalog.read",
        "accounts.user.list", "accounts.user.read",
        "accounts.login_history.read",
        "governance.roles.read", "governance.roles.manage",
        "governance.permissions.read", "governance.permissions.assign",
        "governance.policies.read",
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
    "sub_admin": ["admin", "analytics", "hr", "governance", "audit", "security", "catalog", "orders", "finance", "suppliers", "logistics", "customers", "country", "comms"],
    "moderator": ["admin", "catalog", "orders", "audit", "governance", "analytics", "security"],
    "finance_officer": ["admin", "finance", "orders", "audit", "analytics", "accounts", "customers", "suppliers"],
    "country_manager": ["admin", "country", "catalog", "orders", "suppliers", "finance", "analytics", "audit", "customers", "comms"],
    "auditor": ["admin", "analytics", "hr", "governance", "audit", "security", "catalog", "orders", "finance", "suppliers", "logistics", "customers", "country", "comms", "accounts"],
}


def require_feature(feature: str):
    """Check if the current user has the requested feature.

    Can be used as a FastAPI dependency (``Depends(require_feature("x"))``) or
    called directly in a route handler (``require_feature("x")``).
    Raises HTTPException(403) if the feature is not granted.
    """
    def _check(user=Depends(get_current_user_optional)) -> None:
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
    def _check(user=Depends(get_current_user)) -> None:
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
    def _checker(user=Depends(get_current_user)):
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
