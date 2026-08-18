"""Migration re-export shim for the old controller module `permissions_controller`.
Symbols resolve to their real domain/infra homes.
"""
from __future__ import annotations

from modules.admin.routers.admin import update_role_permissions_route
from modules.admin.routers.admin_permissions_validation import permission_catalog

# Unresolved during migration: permission_hierarchy
