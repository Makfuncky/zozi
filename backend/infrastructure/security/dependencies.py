"""FastAPI auth dependencies: resolve the current user from the bearer token.

Re-export shim -> canonical ``domains.governance.services.security_dependencies``
(P6 merge/shim, no-delete policy). The real implementation now lives in the
``domains`` layer so the infrastructure layer no longer imports ``domains`` at
call sites. This shim keeps every existing importer (including
``infrastructure.utils.dependencies``) resolving with zero edits.
"""
from domains.governance.services.security_dependencies import *  # noqa: F401,F403
from domains.governance.services.security_dependencies import (  # noqa: F401
    logger,
    bearer_scheme,
    _load_user,
    get_current_user,
    get_current_user_optional,
    _require_role,
    require_admin,
    require_super_admin,
    require_employee,
    require_supplier,
    require_logistics,
    require_staff,
    require_treasury_access,
    require_coupon_admin,
    require_roles,
    require_permissions,
)
from infrastructure.database.database import get_db  # noqa: F401
