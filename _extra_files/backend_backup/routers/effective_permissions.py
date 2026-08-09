"""Generated re-export shim.

This module was missing after a refactor that relocated handlers into
subpackage service modules. It re-exports the symbols from their
canonical locations so legacy imports (e.g. `from routers.public_effective_permissions_access import ...`)
keep resolving. Prefer importing from the canonical module directly
in new code.
"""
from __future__ import annotations

from routers.public_permission_primitives_access import (
    COUNTRY_ROLE_PERMISSION_MAP,
    HR_PERMISSION_MAP,
    MAKER_CHECKER_PERMISSIONS,
    approve_permission_change,
    get_effective_permissions,
    invalidate_permission_cache,
    request_permission_change,
)
from routers.public_permissions_access import check_permission

