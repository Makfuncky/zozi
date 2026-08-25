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
    from domains.accounts.services.permissions.permission_service import update_role_permissions
    return update_role_permissions(
        payload["role"], payload["permissions"], payload.get("db"), payload.get("actor") or {},
    )


def _on_bulk_delete_products_admin_requested(payload: dict):
    from domains.governance.services.products.products_service import bulk_delete_products_admin
    return bulk_delete_products_admin(
        payload["product_ids"], payload.get("actor") or {}, payload.get("db"),
    )


def _on_bulk_product_moderation_requested(payload: dict):
    from domains.governance.services.products.products_service import bulk_product_moderation
    return bulk_product_moderation(
        payload["product_ids"], payload["action"], payload.get("note"),
        payload.get("actor") or {}, payload.get("db"),
    )


def _on_delete_product_admin_requested(payload: dict):
    from domains.governance.services.products.products_service import delete_product_admin
    return delete_product_admin(
        payload["product_id"], payload.get("actor") or {}, payload.get("db"),
    )


def _on_restore_product_admin_requested(payload: dict):
    from domains.governance.services.products.products_service import restore_product_admin
    return restore_product_admin(
        payload["product_id"], payload.get("actor") or {}, payload.get("db"),
    )


def _on_toggle_product_badge_requested(payload: dict):
    from domains.governance.services.products.products_service import toggle_product_badge
    return toggle_product_badge(
        payload["product_id"], payload["field"], payload["value"],
        payload.get("actor") or {}, payload.get("db"),
    )


def _on_bulk_delete_users_admin_requested(payload: dict):
    from domains.governance.services.users.users_service_accounts import bulk_delete_users_admin
    return bulk_delete_users_admin(
        payload["user_ids"], payload.get("actor") or {}, payload.get("db"),
    )


def _on_bulk_toggle_users_active_requested(payload: dict):
    from domains.governance.services.users.users_service_accounts import bulk_toggle_users_active
    return bulk_toggle_users_active(
        payload["user_ids"], payload["is_active"], payload.get("actor") or {}, payload.get("db"),
    )


def _on_bulk_update_users_role_requested(payload: dict):
    from domains.governance.services.users.users_service_accounts import bulk_update_users_role
    return bulk_update_users_role(
        payload["user_ids"], payload["role"], payload.get("actor") or {}, payload.get("db"),
    )


def _on_toggle_user_active_requested(payload: dict):
    from domains.governance.services.users.users_service_accounts import toggle_user_active
    return toggle_user_active(
        payload["user_id"], payload.get("actor") or {}, payload.get("db"),
    )


def _on_update_user_role_requested(payload: dict):
    from domains.governance.services.users.users_service_accounts import update_user_role
    return update_user_role(
        payload["user_id"], payload["role"], payload.get("actor") or {}, payload.get("db"),
    )


def _on_force_reset_password_admin_requested(payload: dict):
    from domains.governance.services.users.users_service_accounts import force_reset_password_admin
    return force_reset_password_admin(
        payload["user_id"], payload["new_password"], payload.get("actor") or {}, payload.get("db"),
    )


def _on_bulk_update_staff_accounts_requested(payload: dict):
    from domains.governance.services.users.users_service_accounts import bulk_update_staff_accounts
    return bulk_update_staff_accounts(
        payload["user_ids"], payload["updates"], payload.get("actor") or {}, payload.get("db"),
    )


def _on_create_staff_account_requested(payload: dict):
    from domains.governance.services.users.users_service_accounts import create_staff_account
    return create_staff_account(
        payload["payload"], payload.get("actor") or {}, payload.get("db"),
    )


def _on_delete_staff_account_requested(payload: dict):
    from domains.governance.services.users.users_service_accounts import delete_staff_account
    return delete_staff_account(
        payload["user_id"], payload.get("actor") or {}, payload.get("db"),
    )


def _on_update_staff_account_requested(payload: dict):
    from domains.governance.services.users.users_service_accounts import update_staff_account
    return update_staff_account(
        payload["user_id"], payload["payload"], payload.get("actor") or {}, payload.get("db"),
    )


def _on_bulk_manage_suppliers_requested(payload: dict):
    from domains.governance.services.suppliers.suppliers_service import bulk_manage_suppliers
    return bulk_manage_suppliers(
        payload["supplier_ids"], payload["action"], payload.get("note"),
        payload.get("actor") or {}, payload.get("db"),
        badge_level=payload.get("badge_level"),
    )


def _on_bulk_supplier_verification_requested(payload: dict):
    from domains.governance.services.suppliers.suppliers_service import bulk_supplier_verification
    return bulk_supplier_verification(
        payload["supplier_ids"], payload["action"], payload.get("note"),
        payload.get("actor") or {}, payload.get("db"),
    )


def _on_verify_supplier_requested(payload: dict):
    from domains.governance.services.suppliers.suppliers_service import verify_supplier
    return verify_supplier(
        payload["user_id"], payload.get("note"), payload.get("actor") or {}, payload.get("db"),
    )


def _on_reject_supplier_requested(payload: dict):
    from domains.governance.services.suppliers.suppliers_service import reject_supplier
    return reject_supplier(
        payload["user_id"], payload.get("note"), payload.get("actor") or {}, payload.get("db"),
    )


def _on_order_bulk_delete_requested(payload: dict):
    from domains.governance.services.orders.orders_service import bulk_delete_orders_admin
    return bulk_delete_orders_admin(
        payload["order_ids"], payload.get("actor") or {}, payload.get("db"),
    )


def _on_order_bulk_status_update_requested(payload: dict):
    from domains.governance.services.orders.orders_service import bulk_update_order_status_admin
    return bulk_update_order_status_admin(
        payload["order_ids"], payload["status"], payload.get("actor") or {}, payload.get("db"),
    )


def _on_order_delete_requested(payload: dict):
    from domains.governance.services.orders.orders_service import delete_order_admin
    return delete_order_admin(
        payload["order_id"], payload.get("actor") or {}, payload.get("db"),
    )


def _on_order_refund_requested(payload: dict):
    from domains.governance.services.orders.orders_service import refund_order_admin
    return refund_order_admin(
        payload["order_id"], payload.get("actor") or {}, payload.get("db"),
    )


def _on_order_status_update_requested(payload: dict):
    from domains.governance.services.orders.orders_service import update_order_status
    return update_order_status(
        payload["order_id"], payload["status"], payload.get("actor") or {}, payload.get("db"),
    )


def _on_order_tracking_update_requested(payload: dict):
    from domains.governance.services.orders.orders_service import update_order_tracking
    return update_order_tracking(
        payload["order_id"], payload["tracking_number"], payload.get("actor") or {}, payload.get("db"),
    )


def _on_delete_bank_account_record_requested(payload: dict):
    from domains.governance.services.users.users_service_accounts import delete_bank_account_record_admin
    return delete_bank_account_record_admin(
        payload["kind"], payload["account_id"], payload.get("actor") or {}, payload.get("db"),
    )


def _on_entity_archive_requested(payload: dict):
    from domains.governance.services.settings.misc_service import archive_entity
    return archive_entity(
        payload["entity_type"], payload["entity_id"], payload.get("actor") or {},
        reason=payload.get("reason"), db=payload.get("db"),
    )


def _on_entity_restore_requested(payload: dict):
    from domains.governance.services.settings.misc_service import restore_entity
    return restore_entity(
        payload["entity_type"], payload["entity_id"], payload.get("actor") or {}, payload.get("db"),
    )


def _on_bulk_archive_requested(payload: dict):
    from domains.governance.services.settings.misc_service import archive_entity
    actor = payload.get("actor") or {}
    db = payload.get("db")
    results = []
    for eid in payload["entity_ids"]:
        results.append(archive_entity(
            payload["entity_type"], eid, actor, reason=payload.get("reason"), db=db,
        ))
    return results


def _on_bulk_restore_requested(payload: dict):
    from domains.governance.services.settings.misc_service import restore_entity
    actor = payload.get("actor") or {}
    db = payload.get("db")
    results = []
    for eid in payload["entity_ids"]:
        results.append(restore_entity(payload["entity_type"], eid, actor, db=db))
    return results


# -- register all handlers (importing this module activates them) --
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


# === Merged from accounts/subscribers.py ===

"""Accounts domain event subscribers.

Per Law 3, cross-domain *writes* happen only by consuming events here. This module
registers listeners against the shared ``EventPublisher``. Wire it at boot by calling
``register_accounts_subscribers(publisher)`` from ``lifespan.py`` (kept optional so the
domain stays importable without side effects).
"""


import logging
from typing import Any

from .events import (
    LoginFailed,
    LoginSuccess,
    PasswordForceReset,
    TokenRevoked,
    UserActivated,
    UserCreated,
    UserDeleted,
    UserDeactivated,
    UserRoleChanged,
)

logger = logging.getLogger(__name__)


def _on_user_created(event: UserCreated) -> None:
    logger.info(
        "user created: user_id=%s email=%s role=%s by=%s",
        event.user_id,
        event.email,
        event.role,
        event.created_by,
    )
    # Future: send welcome email, provision default address book, emit comms event.


def _on_user_role_changed(event: UserRoleChanged) -> None:
    logger.info(
        "user role changed: user_id=%s %s -> %s by=%s",
        event.user_id,
        event.old_role,
        event.new_role,
        event.changed_by,
    )


def _on_user_deactivated(event: UserDeactivated) -> None:
    logger.info("user deactivated: user_id=%s reason=%s", event.user_id, event.reason)


def _on_user_activated(event: UserActivated) -> None:
    logger.info("user activated: user_id=%s", event.user_id)


def _on_user_deleted(event: UserDeleted) -> None:
    logger.info(
        "user deleted: user_id=%s hard=%s by=%s",
        event.user_id,
        event.hard_delete,
        event.deleted_by,
    )


def _on_password_force_reset(event: PasswordForceReset) -> None:
    logger.info(
        "password force reset: user_id=%s by=%s",
        event.user_id,
        event.reset_by,
    )


def _on_login_success(event: LoginSuccess) -> None:
    logger.info("login success: user_id=%s country=%s", event.user_id, event.country_code)


def _on_login_failed(event: LoginFailed) -> None:
    logger.warning("login failed: identifier=%s reason=%s", event.identifier, event.reason)


def _on_token_revoked(event: TokenRevoked) -> None:
    logger.info("token revoked: user_id=%s jti=%s reason=%s", event.user_id, event.jti, event.reason)


def register_accounts_subscribers(publisher: Any) -> None:
    """Attach accounts-domain listeners to the shared event publisher."""
    publisher.register_listener(UserCreated, _on_user_created)
    publisher.register_listener(UserRoleChanged, _on_user_role_changed)
    publisher.register_listener(UserDeactivated, _on_user_deactivated)
    publisher.register_listener(UserActivated, _on_user_activated)
    publisher.register_listener(UserDeleted, _on_user_deleted)
    publisher.register_listener(PasswordForceReset, _on_password_force_reset)
    publisher.register_listener(LoginSuccess, _on_login_success)
    publisher.register_listener(LoginFailed, _on_login_failed)
    publisher.register_listener(TokenRevoked, _on_token_revoked)
