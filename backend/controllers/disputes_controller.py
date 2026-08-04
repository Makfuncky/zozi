"""Backward-compat shim: disputes controller now lives in ``controllers.orders.disputes_controller``.

Kept at the root so ``import controllers.disputes_controller`` (used by
``routers/admin.py`` and ``routers/supplier.py``) keeps resolving after the
domain-folder migration.
"""
from controllers.orders.disputes_controller import (
    create_supplier_dispute,
    list_supplier_disputes,
    get_supplier_dispute,
    list_admin_disputes,
    get_admin_dispute,
    update_admin_dispute,
    bulk_update_admin_disputes,
    get_supplier_notification_preferences,
    update_supplier_notification_preferences,
)

__all__ = [
    "create_supplier_dispute",
    "list_supplier_disputes",
    "get_supplier_dispute",
    "list_admin_disputes",
    "get_admin_dispute",
    "update_admin_dispute",
    "bulk_update_admin_disputes",
    "get_supplier_notification_preferences",
    "update_supplier_notification_preferences",
]
