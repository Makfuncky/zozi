"""Migration re-export shim for the old controller module `users_admin_controller`.
Symbols resolve to their real domain/infra homes.
"""
from __future__ import annotations

from modules.admin.routers.admin import bulk_toggle_users_active_route, bulk_update_users_role_route
from infrastructure.database.schemas import CreateStaffAccount, UpdateStaffAccount
from domains.governance.services.country_admin_service import list_staff

# Unresolved during migration: bulk_delete_users_route, bulk_update_staff_accounts_route, create_staff_account_route, delete_staff_account_route, update_staff_account_route, update_user_role_route
