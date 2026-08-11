"""controllers.admin.misc controller.

Business logic is delegated to services.admin.misc_service (routers -> controllers -> services)."""

from services.admin.misc_service import (
    archive_entity, get_audit_log_page, get_available_audit_actions, hard_delete, hard_delete_entity, restore,
    restore_entity, soft_delete
)

__all__ = [
    "archive_entity", "get_audit_log_page", "get_available_audit_actions", "hard_delete", "hard_delete_entity", "restore",
    "restore_entity", "soft_delete"
]
