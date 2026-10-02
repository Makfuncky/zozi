"""Backward-compat shim for legacy import paths.

During the NEW_STRUCTURE migration, auth/permission dependency factories were
relocated to their canonical modules. This shim preserves the old import paths
so that routers and services which have not yet been updated continue to work.

Canonical sources:
- Auth dependencies: ``infrastructure.security.dependencies``
- RBAC gates: ``rbac.dependencies``
- DB session: ``infrastructure.database.database``
"""
from __future__ import annotations

import importlib as _importlib
from typing import Any

_AUTH_SOURCE = "infrastructure.security.dependencies"
_RBAC_SOURCE = "rbac.dependencies"
_DB_SOURCE = "infrastructure.database.database"


def __getattr__(name: str) -> Any:
    if name in {
        "get_current_user",
        "get_current_user_optional",
        "require_admin",
        "require_super_admin",
        "require_employee",
        "require_supplier",
        "require_customer",
        "require_logistics",
        "require_staff",
        "require_treasury_access",
        "require_coupon_admin",
        "require_roles",
        "require_permissions",
        "set_current_user",
        "verify_captcha",
        "_mask_email",
    }:
        mod = _importlib.import_module(_AUTH_SOURCE)
        value = getattr(mod, name)
        globals()[name] = value
        return value
    if name in {
        "require_feature",
        "require_module",
    }:
        mod = _importlib.import_module(_RBAC_SOURCE)
        value = getattr(mod, name)
        globals()[name] = value
        return value
    if name in {
        "get_db",
    }:
        mod = _importlib.import_module(_DB_SOURCE)
        value = getattr(mod, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
