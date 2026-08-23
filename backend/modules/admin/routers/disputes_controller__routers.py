"""controllers.orders.disputes_controller controller.

Business logic is delegated to services.orders.disputes_service (routers -> controllers -> services)."""

from domains.orders.services.disputes_service import (
    _ALLOWED_DISPUTE_TYPES, _ALLOWED_PRIORITIES, _ALLOWED_STATUSES, _PREF_FIELDS, _as_int, _get_or_create_preferences,
    _json_loads, _serialize_dispute, _serialize_preferences, _supplier_id_from_user, bulk_update_admin_disputes, create_supplier_dispute,
    get_admin_dispute, get_supplier_dispute, get_supplier_notification_preferences, list_admin_disputes, list_supplier_disputes, update_admin_dispute,
    update_supplier_notification_preferences
)

__all__ = [
    "_ALLOWED_DISPUTE_TYPES", "_ALLOWED_PRIORITIES", "_ALLOWED_STATUSES", "_PREF_FIELDS", "_as_int", "_get_or_create_preferences",
    "_json_loads", "_serialize_dispute", "_serialize_preferences", "_supplier_id_from_user", "bulk_update_admin_disputes", "create_supplier_dispute",
    "get_admin_dispute", "get_supplier_dispute", "get_supplier_notification_preferences", "list_admin_disputes", "list_supplier_disputes", "update_admin_dispute",
    "update_supplier_notification_preferences"
]
