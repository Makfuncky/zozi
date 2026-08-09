"""Lower-layer permission primitives shared by the routers package.

This module exists to break the circular import between
``routers.public_permissions_access`` and ``routers.public_effective_permissions_access``.

Dependency rule (see documents/architecture/DEPENDENCY_DIRECTION_ADR.md):
    routers.public_permissions_access        -> routers.public_permission_primitives_access
    routers.public_effective_permissions_access -> routers.public_permissions_access (check_permission)
                                  -> routers.public_permission_primitives_access (stubs)
    routers.public_permission_primitives_access -> (nothing)

The following symbols are referenced by legacy code but have NO real
definition anywhere in the codebase. They are stubbed to fail loudly at
call time rather than break import of the importing module. When a real
implementation lands, define it here (or in its canonical service) and
re-export it.
"""
from __future__ import annotations


def _missing_symbol(mod: str, name: str):
    def _f(*_a, **_k):
        raise NotImplementedError(
            f"'{mod}.{name}' is not implemented (refactor gap)")
    return _f


COUNTRY_ROLE_PERMISSION_MAP = _missing_symbol(
    "routers.public_effective_permissions_access", "COUNTRY_ROLE_PERMISSION_MAP")
HR_PERMISSION_MAP = _missing_symbol(
    "routers.public_effective_permissions_access", "HR_PERMISSION_MAP")
MAKER_CHECKER_PERMISSIONS = _missing_symbol(
    "routers.public_effective_permissions_access", "MAKER_CHECKER_PERMISSIONS")
approve_permission_change = _missing_symbol(
    "routers.public_effective_permissions_access", "approve_permission_change")
get_effective_permissions = _missing_symbol(
    "routers.public_effective_permissions_access", "get_effective_permissions")
invalidate_permission_cache = _missing_symbol(
    "routers.public_effective_permissions_access", "invalidate_permission_cache")
request_permission_change = _missing_symbol(
    "routers.public_effective_permissions_access", "request_permission_change")
