"""controllers.orders.disputes_controller controller.

Business logic is delegated to services.orders.disputes_service (routers -> controllers -> services)."""

from domains.finance.services.payments.disputes_service import _ALLOWED_DISPUTE_TYPES
from domains.finance.services.payments.disputes_service import _ALLOWED_PRIORITIES
from domains.finance.services.payments.disputes_service import _ALLOWED_STATUSES
from domains.finance.services.payments.disputes_service import _PREF_FIELDS
from domains.finance.services.payments.disputes_service import _as_int
from domains.finance.services.payments.disputes_service import _get_or_create_preferences
from domains.finance.services.payments.disputes_service import _json_loads
from domains.finance.services.payments.disputes_service import _serialize_dispute
from domains.finance.services.payments.disputes_service import _serialize_preferences
from domains.finance.services.payments.disputes_service import _supplier_id_from_user
from domains.finance.services.payments.disputes_service import bulk_update_admin_disputes
from domains.finance.services.payments.disputes_service import create_supplier_dispute
from domains.finance.services.payments.disputes_service import get_admin_dispute
from domains.finance.services.payments.disputes_service import get_supplier_dispute
from domains.finance.services.payments.disputes_service import get_supplier_notification_preferences
from domains.finance.services.payments.disputes_service import list_admin_disputes
from domains.finance.services.payments.disputes_service import list_supplier_disputes
from domains.finance.services.payments.disputes_service import update_admin_dispute
from domains.finance.services.payments.disputes_service import update_supplier_notification_preferences

__all__ = [
    "_ALLOWED_DISPUTE_TYPES", "_ALLOWED_PRIORITIES", "_ALLOWED_STATUSES", "_PREF_FIELDS", "_as_int", "_get_or_create_preferences",
    "_json_loads", "_serialize_dispute", "_serialize_preferences", "_supplier_id_from_user", "bulk_update_admin_disputes", "create_supplier_dispute",
    "get_admin_dispute", "get_supplier_dispute", "get_supplier_notification_preferences", "list_admin_disputes", "list_supplier_disputes", "update_admin_dispute",
    "update_supplier_notification_preferences"
]
