"""Admin permissions management controller.

Backward-compatible re-exports for importers that reference the old
controllers.admin.permissions path.  Canonical module lives in
controllers/security/permissions.py.
"""
from controllers.security.permissions import (  # noqa: F401
    STAFF_PERMISSION_GROUPS,
    ROLE_PERMISSION_MAP,
    get_staff_permission_catalog,
    load_role_permission_settings,
    get_hierarchy_permissions,
    update_role_permissions,
)
