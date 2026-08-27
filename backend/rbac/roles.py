"""rbac/roles.py - role-to-feature mapping (compatibility shim).

Canonical role definitions live in :mod:`rbac.dependencies`. This module
re-exports them for backward compatibility with code that imports
``rbac.roles.ROLE_FEATURES``.
"""
from __future__ import annotations

from typing import Dict, Set, Tuple

from rbac.dependencies import _ROLE_FEATURES

# Backward-compatible alias: (module, role) -> feature set.
# The canonical structure in rbac/dependencies.py is role -> features;
# this shim converts to the tuple-keyed format for legacy callers.
ROLE_FEATURES: Dict[Tuple[str, str], Set[str]] = {}
for _role, _features in _ROLE_FEATURES.items():
    if _role in ("super_admin", "admin"):
        ROLE_FEATURES[("admin", _role)] = set(_features)
    elif _role == "employee":
        ROLE_FEATURES[("employee", "employee")] = set(_features)
        ROLE_FEATURES[("employee", "finance_manager")] = set(_features)
    elif _role == "staff":
        ROLE_FEATURES[("employee", "staff")] = set(_features)
    elif _role == "supplier":
        ROLE_FEATURES[("supplier", "supplier")] = set(_features)
    elif _role == "logistics_partner":
        ROLE_FEATURES[("logistics", "logistics_partner")] = set(_features)
    elif _role == "customer":
        ROLE_FEATURES[("customer", "customer")] = set(_features)


def is_admin_role(role: str) -> bool:
    """Return True if the role is an admin-level role."""
    return role in {"admin", "sub_admin"}


def validate_user_role(role: str) -> bool:
    """Return True if the role is a valid user role."""
    from rbac.catalog import VALID_USER_ROLES
    return role in VALID_USER_ROLES
