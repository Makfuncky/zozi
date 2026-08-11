"""controllers.admin.users controller.

Business logic is delegated to services.admin.users_service (routers -> controllers -> services)."""

from services.admin.users_service import (
    _DELETABLE_USER_OWNED_MODELS, _DELETE_BLOCKING_SUPPLIER_MODELS, _NULLABLE_USER_REFERENCE_UPDATES, _PROTECTED_EMAILS, _build_list_page_payload, _effective_staff_permissions,
    _serialize_staff_user, bulk_delete_users_admin, bulk_toggle_users_active, bulk_update_staff_accounts, bulk_update_users_role, create_staff_account,
    delete_bank_account_record, delete_staff_account, delete_user_admin, force_reset_password_admin, get_all_users, list_pending_bank_accounts,
    list_staff_accounts, toggle_user_active, update_staff_account, update_user_role, verify_bank_account
)

__all__ = [
    "_DELETABLE_USER_OWNED_MODELS", "_DELETE_BLOCKING_SUPPLIER_MODELS", "_NULLABLE_USER_REFERENCE_UPDATES", "_PROTECTED_EMAILS", "_build_list_page_payload", "_effective_staff_permissions",
    "_serialize_staff_user", "bulk_delete_users_admin", "bulk_toggle_users_active", "bulk_update_staff_accounts", "bulk_update_users_role", "create_staff_account",
    "delete_bank_account_record", "delete_staff_account", "delete_user_admin", "force_reset_password_admin", "get_all_users", "list_pending_bank_accounts",
    "list_staff_accounts", "toggle_user_active", "update_staff_account", "update_user_role", "verify_bank_account"
]
