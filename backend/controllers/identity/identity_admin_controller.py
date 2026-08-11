"""controllers.identity.identity_admin_controller controller.

Business logic is delegated to services.identity.identity_admin_service (routers -> controllers -> services)."""

from services.identity.identity_admin_service import (
    _actor_dict, admin_update_user_api, bulk_toggle_user_active_for_country, delete_user_permanent_for_country, get_profile, get_user_api,
    list_users_api, list_users_for_country, logger, update_profile, update_user_for_country
)

__all__ = [
    "_actor_dict", "admin_update_user_api", "bulk_toggle_user_active_for_country", "delete_user_permanent_for_country", "get_profile", "get_user_api",
    "list_users_api", "list_users_for_country", "logger", "update_profile", "update_user_for_country"
]
