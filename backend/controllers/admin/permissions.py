"""controllers.admin.permissions controller.

Business logic is delegated to services.admin.permissions_service (routers -> controllers -> services)."""

from services.admin.permissions_service import (
    STAFF_PERMISSION_GROUPS, get_hierarchy_permissions, get_staff_permission_catalog, load_role_permission_settings, update_role_permissions
)

__all__ = [
    "STAFF_PERMISSION_GROUPS", "get_hierarchy_permissions", "get_staff_permission_catalog", "load_role_permission_settings", "update_role_permissions"
]
