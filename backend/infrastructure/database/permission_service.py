"""Permission service re-export shim.

The canonical implementation lives in domains.governance.services.permissions.permission_service.
This shim exists because many auto-migrated modules (accounts/*, country/*, governance/*, customers/*)
import permission_service from infrastructure.database.
"""
from domains.governance.services.permissions.permission_service import *  # noqa: F401,F403
from domains.governance.services.permissions.permission_service import (
    _log_audit,
    assign_permission_to_role,
    check_user_permission,
    create_category,
    create_permission,
    delete_category,
    delete_permission,
    get_role_permissions,
    list_categories,
    list_permissions,
    revoke_permission_from_role,
    set_user_permission_override,
    update_category,
)
