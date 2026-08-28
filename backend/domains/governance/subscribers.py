"""governance domain - AXIS 2 event subscribers (Law 3: react to cross-domain intents).

Registers handlers on the in-process ``event_bus`` so the governance domain can
react to the ``gov.*_requested`` intents published by module routers. Each handler
extracts the intent payload and delegates to the canonical governance service
function that performs the actual write.

Importing this module registers the handlers. It is wired from the governance
package ``__init__.py`` so handlers are active as soon as the domain is imported.
"""

from __future__ import annotations

import logging

from infrastructure.messaging.events.event_bus import subscribe

from .events import (
    EVENT_GOV_UPDATE_ROLE_PERMISSIONS_REQUESTED,
    EVENT_GOV_BULK_DELETE_PRODUCTS_ADMIN_REQUESTED,
    EVENT_GOV_BULK_PRODUCT_MODERATION_REQUESTED,
    EVENT_GOV_DELETE_PRODUCT_ADMIN_REQUESTED,
    EVENT_GOV_RESTORE_PRODUCT_ADMIN_REQUESTED,
    EVENT_GOV_TOGGLE_PRODUCT_BADGE_REQUESTED,
    EVENT_GOV_BULK_DELETE_USERS_ADMIN_REQUESTED,
    EVENT_GOV_BULK_TOGGLE_USERS_ACTIVE_REQUESTED,
    EVENT_GOV_BULK_UPDATE_USERS_ROLE_REQUESTED,
    EVENT_GOV_TOGGLE_USER_ACTIVE_REQUESTED,
    EVENT_GOV_UPDATE_USER_ROLE_REQUESTED,
    EVENT_GOV_FORCE_RESET_PASSWORD_ADMIN_REQUESTED,
    EVENT_GOV_BULK_UPDATE_STAFF_ACCOUNTS_REQUESTED,
    EVENT_GOV_CREATE_STAFF_ACCOUNT_REQUESTED,
    EVENT_GOV_DELETE_STAFF_ACCOUNT_REQUESTED,
    EVENT_GOV_UPDATE_STAFF_ACCOUNT_REQUESTED,
    EVENT_GOV_BULK_MANAGE_SUPPLIERS_REQUESTED,
    EVENT_GOV_BULK_SUPPLIER_VERIFICATION_REQUESTED,
    EVENT_GOV_VERIFY_SUPPLIER_REQUESTED,
    EVENT_GOV_REJECT_SUPPLIER_REQUESTED,
    EVENT_GOV_ORDER_BULK_DELETE_REQUESTED,
    EVENT_GOV_ORDER_BULK_STATUS_UPDATE_REQUESTED,
    EVENT_GOV_ORDER_DELETE_REQUESTED,
    EVENT_GOV_ORDER_REFUND_REQUESTED,
    EVENT_GOV_ORDER_STATUS_UPDATE_REQUESTED,
    EVENT_GOV_ORDER_TRACKING_UPDATE_REQUESTED,
    EVENT_GOV_DELETE_BANK_ACCOUNT_RECORD_REQUESTED,
    EVENT_GOV_ENTITY_ARCHIVE_REQUESTED,
    EVENT_GOV_ENTITY_RESTORE_REQUESTED,
    EVENT_GOV_BULK_ARCHIVE_REQUESTED,
    EVENT_GOV_BULK_RESTORE_REQUESTED,
)

logger = logging.getLogger(__name__)


def _on_update_role_permissions_requested(payload: dict):
from domains.accounts.ports import force_reset_password_admin, update_role_permissions
    return update_role_permissions(
        payload["role"], payload["permissions"], payload.get("actor") or {},
    )


def _on_bulk_delete_products_admin_requested(payload: dict):
    # TODO: Module not yet created
    # from domains.governance.services.products.products_service import bulk_delete_products_admin
    logger.warning("bulk_delete_products_admin not implemented")
    return None


def _on_bulk_product_moderation_requested(payload: dict):
    # TODO: Module not yet created
    # from domains.governance.services.products.products_service import bulk_product_moderation
    logger.warning("bulk_product_moderation not implemented")
    return None


def _on_delete_product_admin_requested(payload: dict):
    # TODO: Module not yet created
    # from domains.governance.services.products.products_service import delete_product_admin
    logger.warning("delete_product_admin not implemented")
    return None


def _on_restore_product_admin_requested(payload: dict):
    # TODO: Module not yet created
    # from domains.governance.services.products.products_service import restore_product_admin
    logger.warning("restore_product_admin not implemented")
    return None


def _on_toggle_product_badge_requested(payload: dict):
    # TODO: Module not yet created
    # from domains.governance.services.products.products_service import toggle_product_badge
    logger.warning("toggle_product_badge not implemented")
    return None


def _on_bulk_delete_users_admin_requested(payload: dict):
    # TODO: Module not yet created
    # from domains.governance.services.users.users_service_accounts import bulk_delete_users_admin
    logger.warning("bulk_delete_users_admin not implemented")
    return None


def _on_bulk_toggle_users_active_requested(payload: dict):
    # TODO: Module not yet created
    # from domains.governance.services.users.users_service_accounts import bulk_toggle_users_active
    logger.warning("bulk_toggle_users_active not implemented")
    return None


def _on_bulk_update_users_role_requested(payload: dict):
    # TODO: Module not yet created
    # from domains.governance.services.users.users_service_accounts import bulk_update_users_role
    logger.warning("bulk_update_users_role not implemented")
    return None


def _on_toggle_user_active_requested(payload: dict):
    # TODO: Module not yet created
    # from domains.governance.services.users.users_service_accounts import toggle_user_active
    logger.warning("toggle_user_active not implemented")
    return None


def _on_update_user_role_requested(payload: dict):
    # TODO: Module not yet created
    # from domains.governance.services.users.users_service_accounts import update_user_role
    logger.warning("update_user_role not implemented")
    return None


def _on_force_reset_password_admin_requested(payload: dict):
    return force_reset_password_admin(
        payload["user_id"], payload["password_hash"], payload.get("actor") or {},
    )


def _on_bulk_update_staff_accounts_requested(payload: dict):
    # TODO: Module not yet created
    # from domains.governance.services.users.users_service_accounts import bulk_update_staff_accounts
    logger.warning("bulk_update_staff_accounts not implemented")
    return None


def _on_create_staff_account_requested(payload: dict):
    # TODO: Module not yet created
    # from domains.governance.services.users.users_service_accounts import create_staff_account
    logger.warning("create_staff_account not implemented")
    return None


def _on_delete_staff_account_requested(payload: dict):
    # TODO: Module not yet created
    # from domains.governance.services.users.users_service_accounts import delete_staff_account
    logger.warning("delete_staff_account not implemented")
    return None


def _on_update_staff_account_requested(payload: dict):
    # TODO: Module not yet created
    # from domains.governance.services.users.users_service_accounts import update_staff_account
    logger.warning("update_staff_account not implemented")
    return None


def _on_bulk_manage_suppliers_requested(payload: dict):
    # TODO: Module not yet created
    # from domains.governance.services.suppliers.suppliers_service import bulk_manage_suppliers
    logger.warning("bulk_manage_suppliers not implemented")
    return None


def _on_bulk_supplier_verification_requested(payload: dict):
    # TODO: Module not yet created
    # from domains.governance.services.suppliers.suppliers_service import bulk_supplier_verification
    logger.warning("bulk_supplier_verification not implemented")
    return None


def _on_verify_supplier_requested(payload: dict):
    # TODO: Module not yet created
    # from domains.governance.services.suppliers.suppliers_service import verify_supplier
    logger.warning("verify_supplier not implemented")
    return None


def _on_reject_supplier_requested(payload: dict):
    # TODO: Module not yet created
    # from domains.governance.services.suppliers.suppliers_service import reject_supplier
    logger.warning("reject_supplier not implemented")
    return None


def _on_order_bulk_delete_requested(payload: dict):
    # TODO: Module not yet created
    # from domains.governance.services.orders.orders_service import bulk_delete_orders_admin
    logger.warning("bulk_delete_orders_admin not implemented")
    return None


def _on_order_bulk_status_update_requested(payload: dict):
    # TODO: Module not yet created
    # from domains.governance.services.orders.orders_service import bulk_update_order_status_admin
    logger.warning("bulk_update_order_status_admin not implemented")
    return None


def _on_order_delete_requested(payload: dict):
    # TODO: Module not yet created
    # from domains.governance.services.orders.orders_service import delete_order_admin
    logger.warning("delete_order_admin not implemented")
    return None


def _on_order_refund_requested(payload: dict):
    # TODO: Module not yet created
    # from domains.governance.services.orders.orders_service import refund_order_admin
    logger.warning("refund_order_admin not implemented")
    return None


def _on_order_status_update_requested(payload: dict):
    # TODO: Module not yet created
    # from domains.governance.services.orders.orders_service import update_order_status
    logger.warning("update_order_status not implemented")
    return None


def _on_order_tracking_update_requested(payload: dict):
    # TODO: Module not yet created
    # from domains.governance.services.orders.orders_service import update_order_tracking
    logger.warning("update_order_tracking not implemented")
    return None


def _on_delete_bank_account_record_requested(payload: dict):
    # TODO: Module not yet created
    # from domains.governance.services.users.users_service_accounts import delete_bank_account_record_admin
    logger.warning("delete_bank_account_record_admin not implemented")
    return None


def _on_entity_archive_requested(payload: dict):
    from domains.governance.services.settings.misc_service import archive_entity
    return archive_entity(
        payload["entity_type"], payload["entity_id"], payload.get("actor") or {},
        reason=payload.get("reason"),
    )


def _on_entity_restore_requested(payload: dict):
    from domains.governance.services.settings.misc_service import restore_entity
    return restore_entity(
        payload["entity_type"], payload["entity_id"], payload.get("actor") or {},
    )


def _on_bulk_archive_requested(payload: dict):
    from domains.governance.services.settings.misc_service import archive_entity
    actor = payload.get("actor") or {}
    results = []
    for eid in payload["entity_ids"]:
        results.append(archive_entity(
            payload["entity_type"], eid, actor, reason=payload.get("reason"),
        ))
    return results


def _on_bulk_restore_requested(payload: dict):
    from domains.governance.services.settings.misc_service import restore_entity
    actor = payload.get("actor") or {}
    results = []
    for eid in payload["entity_ids"]:
        results.append(restore_entity(payload["entity_type"], eid, actor))
    return results


def register_governance_subscribers():
    """Register all governance event subscribers.

    Call this at app startup (e.g., from lifespan.py) to activate handlers.
    Kept as a function (not import-time side effects) so the module stays
    importable without triggering subscriptions.
    """
    subscribe(EVENT_GOV_UPDATE_ROLE_PERMISSIONS_REQUESTED, _on_update_role_permissions_requested)
    subscribe(EVENT_GOV_BULK_DELETE_PRODUCTS_ADMIN_REQUESTED, _on_bulk_delete_products_admin_requested)
    subscribe(EVENT_GOV_BULK_PRODUCT_MODERATION_REQUESTED, _on_bulk_product_moderation_requested)
    subscribe(EVENT_GOV_DELETE_PRODUCT_ADMIN_REQUESTED, _on_delete_product_admin_requested)
    subscribe(EVENT_GOV_RESTORE_PRODUCT_ADMIN_REQUESTED, _on_restore_product_admin_requested)
    subscribe(EVENT_GOV_TOGGLE_PRODUCT_BADGE_REQUESTED, _on_toggle_product_badge_requested)
    subscribe(EVENT_GOV_BULK_DELETE_USERS_ADMIN_REQUESTED, _on_bulk_delete_users_admin_requested)
    subscribe(EVENT_GOV_BULK_TOGGLE_USERS_ACTIVE_REQUESTED, _on_bulk_toggle_users_active_requested)
    subscribe(EVENT_GOV_BULK_UPDATE_USERS_ROLE_REQUESTED, _on_bulk_update_users_role_requested)
    subscribe(EVENT_GOV_TOGGLE_USER_ACTIVE_REQUESTED, _on_toggle_user_active_requested)
    subscribe(EVENT_GOV_UPDATE_USER_ROLE_REQUESTED, _on_update_user_role_requested)
    subscribe(EVENT_GOV_FORCE_RESET_PASSWORD_ADMIN_REQUESTED, _on_force_reset_password_admin_requested)
    subscribe(EVENT_GOV_BULK_UPDATE_STAFF_ACCOUNTS_REQUESTED, _on_bulk_update_staff_accounts_requested)
    subscribe(EVENT_GOV_CREATE_STAFF_ACCOUNT_REQUESTED, _on_create_staff_account_requested)
    subscribe(EVENT_GOV_DELETE_STAFF_ACCOUNT_REQUESTED, _on_delete_staff_account_requested)
    subscribe(EVENT_GOV_UPDATE_STAFF_ACCOUNT_REQUESTED, _on_update_staff_account_requested)
    subscribe(EVENT_GOV_BULK_MANAGE_SUPPLIERS_REQUESTED, _on_bulk_manage_suppliers_requested)
    subscribe(EVENT_GOV_BULK_SUPPLIER_VERIFICATION_REQUESTED, _on_bulk_supplier_verification_requested)
    subscribe(EVENT_GOV_VERIFY_SUPPLIER_REQUESTED, _on_verify_supplier_requested)
    subscribe(EVENT_GOV_REJECT_SUPPLIER_REQUESTED, _on_reject_supplier_requested)
    subscribe(EVENT_GOV_ORDER_BULK_DELETE_REQUESTED, _on_order_bulk_delete_requested)
    subscribe(EVENT_GOV_ORDER_BULK_STATUS_UPDATE_REQUESTED, _on_order_bulk_status_update_requested)
    subscribe(EVENT_GOV_ORDER_DELETE_REQUESTED, _on_order_delete_requested)
    subscribe(EVENT_GOV_ORDER_REFUND_REQUESTED, _on_order_refund_requested)
    subscribe(EVENT_GOV_ORDER_STATUS_UPDATE_REQUESTED, _on_order_status_update_requested)
    subscribe(EVENT_GOV_ORDER_TRACKING_UPDATE_REQUESTED, _on_order_tracking_update_requested)
    subscribe(EVENT_GOV_DELETE_BANK_ACCOUNT_RECORD_REQUESTED, _on_delete_bank_account_record_requested)
    subscribe(EVENT_GOV_ENTITY_ARCHIVE_REQUESTED, _on_entity_archive_requested)
    subscribe(EVENT_GOV_ENTITY_RESTORE_REQUESTED, _on_entity_restore_requested)
    subscribe(EVENT_GOV_BULK_ARCHIVE_REQUESTED, _on_bulk_archive_requested)
    subscribe(EVENT_GOV_BULK_RESTORE_REQUESTED, _on_bulk_restore_requested)


__all__ = [
    "_on_update_role_permissions_requested",
    "_on_bulk_delete_products_admin_requested",
    "_on_bulk_product_moderation_requested",
    "_on_delete_product_admin_requested",
    "_on_restore_product_admin_requested",
    "_on_toggle_product_badge_requested",
    "_on_bulk_delete_users_admin_requested",
    "_on_bulk_toggle_users_active_requested",
    "_on_bulk_update_users_role_requested",
    "_on_toggle_user_active_requested",
    "_on_update_user_role_requested",
    "_on_force_reset_password_admin_requested",
    "_on_bulk_update_staff_accounts_requested",
    "_on_create_staff_account_requested",
    "_on_delete_staff_account_requested",
    "_on_update_staff_account_requested",
    "_on_bulk_manage_suppliers_requested",
    "_on_bulk_supplier_verification_requested",
    "_on_verify_supplier_requested",
    "_on_reject_supplier_requested",
    "_on_order_bulk_delete_requested",
    "_on_order_bulk_status_update_requested",
    "_on_order_delete_requested",
    "_on_order_refund_requested",
    "_on_order_status_update_requested",
    "_on_order_tracking_update_requested",
    "_on_delete_bank_account_record_requested",
    "_on_entity_archive_requested",
    "_on_entity_restore_requested",
    "_on_bulk_archive_requested",
    "_on_bulk_restore_requested",
]
