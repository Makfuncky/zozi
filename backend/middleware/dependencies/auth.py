"""FastAPI auth dependencies (canonical home).

Relocated from ``domains.accounts.services.auth.security_dependencies`` per
ARCHITECTURE_DIAGRAM.md Law 1 — these helpers live in ``middleware/dependencies``
so that infrastructure modules no longer reach up to ``domains`` to obtain auth
helpers via ``middleware.dependencies.auth``.

The previous ``middleware.dependencies.auth`` shim is preserved as a
backward-compat re-export so existing call sites keep working. New code should
import from here:

    from middleware.dependencies.auth import get_current_user, require_admin
"""
from __future__ import annotations

# Backward-compat: ``security_dependencies`` is the original module that
# exposed all of these symbols. Re-export from its new location so the
# historical surface keeps working without duplication.
from domains.accounts.services.auth.security_dependencies import (  # noqa: F401
    bearer_scheme,
    get_current_user,
    get_current_user_optional,
    require_admin,
    require_coupon_admin,
    require_customer,
    require_employee,
    require_logistics,
    require_permissions,
    require_roles,
    require_staff,
    require_super_admin,
    require_supplier,
    require_treasury_access,
    start_otp,
    verify_otp,
)

__all__ = [
    "bearer_scheme",
    "get_current_user",
    "get_current_user_optional",
    "require_admin",
    "require_coupon_admin",
    "require_customer",
    "require_employee",
    "require_logistics",
    "require_permissions",
    "require_roles",
    "require_staff",
    "require_super_admin",
    "require_supplier",
    "require_treasury_access",
    "start_otp",
    "verify_otp",
]