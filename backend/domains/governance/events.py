"""governance domain - AXIS 2 event surface (Law 3: cross-domain writes via events).

The governance domain owns the ``governance`` schema and the admin-control
surface for products, users, suppliers, orders, staff, and permissions. Module
routers publish ``gov.*_requested`` intent events here; governance subscribers
handle those intents by calling the real service functions. This keeps module
routers thin (Law 2) and routes all cross-domain writes through events (Law 3).

Transport is the sanctioned in-process ``event_bus`` (circuit-exempt data layer).
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from infrastructure.messaging.events.event_bus import publish

logger = logging.getLogger(__name__)

# -- Intent events: published by module routers, handled by governance subscribers --
EVENT_GOV_UPDATE_ROLE_PERMISSIONS_REQUESTED = "gov.update_role_permissions_requested"
EVENT_GOV_BULK_DELETE_PRODUCTS_ADMIN_REQUESTED = "gov.bulk_delete_products_admin_requested"
EVENT_GOV_BULK_PRODUCT_MODERATION_REQUESTED = "gov.bulk_product_moderation_requested"
EVENT_GOV_DELETE_PRODUCT_ADMIN_REQUESTED = "gov.delete_product_admin_requested"
EVENT_GOV_RESTORE_PRODUCT_ADMIN_REQUESTED = "gov.restore_product_admin_requested"
EVENT_GOV_TOGGLE_PRODUCT_BADGE_REQUESTED = "gov.toggle_product_badge_requested"
EVENT_GOV_BULK_DELETE_USERS_ADMIN_REQUESTED = "gov.bulk_delete_users_admin_requested"
EVENT_GOV_BULK_TOGGLE_USERS_ACTIVE_REQUESTED = "gov.bulk_toggle_users_active_requested"
EVENT_GOV_BULK_UPDATE_USERS_ROLE_REQUESTED = "gov.bulk_update_users_role_requested"
EVENT_GOV_TOGGLE_USER_ACTIVE_REQUESTED = "gov.toggle_user_active_requested"
EVENT_GOV_UPDATE_USER_ROLE_REQUESTED = "gov.update_user_role_requested"
EVENT_GOV_FORCE_RESET_PASSWORD_ADMIN_REQUESTED = "gov.force_reset_password_admin_requested"
EVENT_GOV_BULK_UPDATE_STAFF_ACCOUNTS_REQUESTED = "gov.bulk_update_staff_accounts_requested"
EVENT_GOV_CREATE_STAFF_ACCOUNT_REQUESTED = "gov.create_staff_account_requested"
EVENT_GOV_DELETE_STAFF_ACCOUNT_REQUESTED = "gov.delete_staff_account_requested"
EVENT_GOV_UPDATE_STAFF_ACCOUNT_REQUESTED = "gov.update_staff_account_requested"
EVENT_GOV_BULK_MANAGE_SUPPLIERS_REQUESTED = "gov.bulk_manage_suppliers_requested"
EVENT_GOV_BULK_SUPPLIER_VERIFICATION_REQUESTED = "gov.bulk_supplier_verification_requested"
EVENT_GOV_VERIFY_SUPPLIER_REQUESTED = "gov.verify_supplier_requested"
EVENT_GOV_REJECT_SUPPLIER_REQUESTED = "gov.reject_supplier_requested"
EVENT_GOV_ORDER_BULK_DELETE_REQUESTED = "gov.order_bulk_delete_requested"
EVENT_GOV_ORDER_BULK_STATUS_UPDATE_REQUESTED = "gov.order_bulk_status_update_requested"
EVENT_GOV_ORDER_DELETE_REQUESTED = "gov.order_delete_requested"
EVENT_GOV_ORDER_REFUND_REQUESTED = "gov.order_refund_requested"
EVENT_GOV_ORDER_STATUS_UPDATE_REQUESTED = "gov.order_status_update_requested"
EVENT_GOV_ORDER_TRACKING_UPDATE_REQUESTED = "gov.order_tracking_update_requested"
EVENT_GOV_DELETE_BANK_ACCOUNT_RECORD_REQUESTED = "gov.delete_bank_account_record_requested"
EVENT_GOV_ENTITY_ARCHIVE_REQUESTED = "gov.entity_archive_requested"
EVENT_GOV_ENTITY_RESTORE_REQUESTED = "gov.entity_restore_requested"
EVENT_GOV_BULK_ARCHIVE_REQUESTED = "gov.bulk_archive_requested"
EVENT_GOV_BULK_RESTORE_REQUESTED = "gov.bulk_restore_requested"


def _event_id() -> str:
    return uuid.uuid4().hex


def _now_iso() -> str:
    return datetime.utcnow().isoformat()


def publish_gov_update_role_permissions_requested(
    role: str, permissions: List[str], db: object = None, actor: Optional[dict] = None
) -> Any:
    """Request a role-permission map update."""
    payload = {
        "event_id": _event_id(),
        "timestamp": _now_iso(),
        "role": role,
        "permissions": permissions,
        "db": db,
        "actor": actor,
    }
    logger.info("gov: update_role_permissions_requested role=%s", role)
    return publish(EVENT_GOV_UPDATE_ROLE_PERMISSIONS_REQUESTED, payload, propagate=True)


def publish_gov_bulk_delete_products_admin_requested(
    product_ids: List[int], actor: dict, db: object = None
) -> Any:
    payload = {
        "event_id": _event_id(), "timestamp": _now_iso(),
        "product_ids": product_ids, "actor": actor, "db": db,
    }
    logger.info("gov: bulk_delete_products_admin_requested count=%d", len(product_ids))
    return publish(EVENT_GOV_BULK_DELETE_PRODUCTS_ADMIN_REQUESTED, payload, propagate=True)


def publish_gov_bulk_product_moderation_requested(
    product_ids: List[int], action: str, note: Optional[str], actor: dict, db: object = None
) -> Any:
    payload = {
        "event_id": _event_id(), "timestamp": _now_iso(),
        "product_ids": product_ids, "action": action, "note": note, "actor": actor, "db": db,
    }
    logger.info("gov: bulk_product_moderation_requested count=%d action=%s", len(product_ids), action)
    return publish(EVENT_GOV_BULK_PRODUCT_MODERATION_REQUESTED, payload, propagate=True)


def publish_gov_delete_product_admin_requested(
    product_id: int, actor: dict, db: object = None
) -> Any:
    payload = {
        "event_id": _event_id(), "timestamp": _now_iso(),
        "product_id": product_id, "actor": actor, "db": db,
    }
    logger.info("gov: delete_product_admin_requested product_id=%d", product_id)
    return publish(EVENT_GOV_DELETE_PRODUCT_ADMIN_REQUESTED, payload, propagate=True)


def publish_gov_restore_product_admin_requested(
    product_id: int, actor: dict, db: object = None
) -> Any:
    payload = {
        "event_id": _event_id(), "timestamp": _now_iso(),
        "product_id": product_id, "actor": actor, "db": db,
    }
    logger.info("gov: restore_product_admin_requested product_id=%d", product_id)
    return publish(EVENT_GOV_RESTORE_PRODUCT_ADMIN_REQUESTED, payload, propagate=True)


def publish_gov_toggle_product_badge_requested(
    product_id: int, field: str, value: bool, actor: dict, db: object = None
) -> Any:
    payload = {
        "event_id": _event_id(), "timestamp": _now_iso(),
        "product_id": product_id, "field": field, "value": value, "actor": actor, "db": db,
    }
    logger.info("gov: toggle_product_badge_requested product_id=%d field=%s", product_id, field)
    return publish(EVENT_GOV_TOGGLE_PRODUCT_BADGE_REQUESTED, payload, propagate=True)


def publish_gov_bulk_delete_users_admin_requested(
    user_ids: List[int], actor: dict, db: object = None
) -> Any:
    payload = {
        "event_id": _event_id(), "timestamp": _now_iso(),
        "user_ids": user_ids, "actor": actor, "db": db,
    }
    logger.info("gov: bulk_delete_users_admin_requested count=%d", len(user_ids))
    return publish(EVENT_GOV_BULK_DELETE_USERS_ADMIN_REQUESTED, payload, propagate=True)


def publish_gov_bulk_toggle_users_active_requested(
    user_ids: List[int], is_active: bool, actor: dict, db: object = None
) -> Any:
    payload = {
        "event_id": _event_id(), "timestamp": _now_iso(),
        "user_ids": user_ids, "is_active": is_active, "actor": actor, "db": db,
    }
    logger.info("gov: bulk_toggle_users_active_requested count=%d is_active=%s", len(user_ids), is_active)
    return publish(EVENT_GOV_BULK_TOGGLE_USERS_ACTIVE_REQUESTED, payload, propagate=True)


def publish_gov_bulk_update_users_role_requested(
    user_ids: List[int], role: str, actor: dict, db: object = None
) -> Any:
    payload = {
        "event_id": _event_id(), "timestamp": _now_iso(),
        "user_ids": user_ids, "role": role, "actor": actor, "db": db,
    }
    logger.info("gov: bulk_update_users_role_requested count=%d role=%s", len(user_ids), role)
    return publish(EVENT_GOV_BULK_UPDATE_USERS_ROLE_REQUESTED, payload, propagate=True)


def publish_gov_toggle_user_active_requested(
    user_id: int, actor: dict, db: object = None
) -> Any:
    payload = {
        "event_id": _event_id(), "timestamp": _now_iso(),
        "user_id": user_id, "actor": actor, "db": db,
    }
    logger.info("gov: toggle_user_active_requested user_id=%d", user_id)
    return publish(EVENT_GOV_TOGGLE_USER_ACTIVE_REQUESTED, payload, propagate=True)


def publish_gov_update_user_role_requested(
    user_id: int, role: str, actor: dict, db: object = None
) -> Any:
    payload = {
        "event_id": _event_id(), "timestamp": _now_iso(),
        "user_id": user_id, "role": role, "actor": actor, "db": db,
    }
    logger.info("gov: update_user_role_requested user_id=%d role=%s", user_id, role)
    return publish(EVENT_GOV_UPDATE_USER_ROLE_REQUESTED, payload, propagate=True)


def publish_gov_force_reset_password_admin_requested(
    user_id: int, new_password: str, actor: dict, db: object = None
) -> Any:
    payload = {
        "event_id": _event_id(), "timestamp": _now_iso(),
        "user_id": user_id, "new_password": new_password, "actor": actor, "db": db,
    }
    logger.info("gov: force_reset_password_admin_requested user_id=%d", user_id)
    return publish(EVENT_GOV_FORCE_RESET_PASSWORD_ADMIN_REQUESTED, payload, propagate=True)


def publish_gov_bulk_update_staff_accounts_requested(
    user_ids: List[int], updates: object, actor: dict, db: object = None
) -> Any:
    payload = {
        "event_id": _event_id(), "timestamp": _now_iso(),
        "user_ids": user_ids, "updates": updates, "actor": actor, "db": db,
    }
    logger.info("gov: bulk_update_staff_accounts_requested count=%d", len(user_ids))
    return publish(EVENT_GOV_BULK_UPDATE_STAFF_ACCOUNTS_REQUESTED, payload, propagate=True)


def publish_gov_create_staff_account_requested(
    payload_data: object, actor: dict, db: object = None
) -> Any:
    payload = {
        "event_id": _event_id(), "timestamp": _now_iso(),
        "payload": payload_data, "actor": actor, "db": db,
    }
    logger.info("gov: create_staff_account_requested")
    return publish(EVENT_GOV_CREATE_STAFF_ACCOUNT_REQUESTED, payload, propagate=True)


def publish_gov_delete_staff_account_requested(
    user_id: int, actor: dict, db: object = None
) -> Any:
    payload = {
        "event_id": _event_id(), "timestamp": _now_iso(),
        "user_id": user_id, "actor": actor, "db": db,
    }
    logger.info("gov: delete_staff_account_requested user_id=%d", user_id)
    return publish(EVENT_GOV_DELETE_STAFF_ACCOUNT_REQUESTED, payload, propagate=True)


def publish_gov_update_staff_account_requested(
    user_id: int, payload_data: object, actor: dict, db: object = None
) -> Any:
    payload = {
        "event_id": _event_id(), "timestamp": _now_iso(),
        "user_id": user_id, "payload": payload_data, "actor": actor, "db": db,
    }
    logger.info("gov: update_staff_account_requested user_id=%d", user_id)
    return publish(EVENT_GOV_UPDATE_STAFF_ACCOUNT_REQUESTED, payload, propagate=True)


def publish_gov_bulk_manage_suppliers_requested(
    supplier_ids: List[int], action: str, note: Optional[str], actor: dict,
    db: object = None, badge_level: Optional[str] = None,
) -> Any:
    payload = {
        "event_id": _event_id(), "timestamp": _now_iso(),
        "supplier_ids": supplier_ids, "action": action, "note": note,
        "badge_level": badge_level, "actor": actor, "db": db,
    }
    logger.info("gov: bulk_manage_suppliers_requested count=%d action=%s", len(supplier_ids), action)
    return publish(EVENT_GOV_BULK_MANAGE_SUPPLIERS_REQUESTED, payload, propagate=True)


def publish_gov_bulk_supplier_verification_requested(
    supplier_ids: List[int], action: str, note: Optional[str], actor: dict, db: object = None
) -> Any:
    payload = {
        "event_id": _event_id(), "timestamp": _now_iso(),
        "supplier_ids": supplier_ids, "action": action, "note": note, "actor": actor, "db": db,
    }
    logger.info("gov: bulk_supplier_verification_requested count=%d", len(supplier_ids))
    return publish(EVENT_GOV_BULK_SUPPLIER_VERIFICATION_REQUESTED, payload, propagate=True)


def publish_gov_verify_supplier_requested(
    user_id: int, note: Optional[str], actor: dict, db: object = None
) -> Any:
    payload = {
        "event_id": _event_id(), "timestamp": _now_iso(),
        "user_id": user_id, "note": note, "actor": actor, "db": db,
    }
    logger.info("gov: verify_supplier_requested user_id=%d", user_id)
    return publish(EVENT_GOV_VERIFY_SUPPLIER_REQUESTED, payload, propagate=True)


def publish_gov_reject_supplier_requested(
    user_id: int, note: Optional[str], actor: dict, db: object = None
) -> Any:
    payload = {
        "event_id": _event_id(), "timestamp": _now_iso(),
        "user_id": user_id, "note": note, "actor": actor, "db": db,
    }
    logger.info("gov: reject_supplier_requested user_id=%d", user_id)
    return publish(EVENT_GOV_REJECT_SUPPLIER_REQUESTED, payload, propagate=True)


def publish_gov_order_bulk_delete_requested(
    order_ids: List[int], actor: dict, db: object = None
) -> Any:
    payload = {
        "event_id": _event_id(), "timestamp": _now_iso(),
        "order_ids": order_ids, "actor": actor, "db": db,
    }
    logger.info("gov: order_bulk_delete_requested count=%d", len(order_ids))
    return publish(EVENT_GOV_ORDER_BULK_DELETE_REQUESTED, payload, propagate=True)


def publish_gov_order_bulk_status_update_requested(
    order_ids: List[int], status: str, actor: dict, db: object = None
) -> Any:
    payload = {
        "event_id": _event_id(), "timestamp": _now_iso(),
        "order_ids": order_ids, "status": status, "actor": actor, "db": db,
    }
    logger.info("gov: order_bulk_status_update_requested count=%d status=%s", len(order_ids), status)
    return publish(EVENT_GOV_ORDER_BULK_STATUS_UPDATE_REQUESTED, payload, propagate=True)


def publish_gov_order_delete_requested(
    order_id: int, actor: dict, db: object = None
) -> Any:
    payload = {
        "event_id": _event_id(), "timestamp": _now_iso(),
        "order_id": order_id, "actor": actor, "db": db,
    }
    logger.info("gov: order_delete_requested order_id=%d", order_id)
    return publish(EVENT_GOV_ORDER_DELETE_REQUESTED, payload, propagate=True)


def publish_gov_order_refund_requested(
    order_id: int, actor: dict, db: object = None
) -> Any:
    payload = {
        "event_id": _event_id(), "timestamp": _now_iso(),
        "order_id": order_id, "actor": actor, "db": db,
    }
    logger.info("gov: order_refund_requested order_id=%d", order_id)
    return publish(EVENT_GOV_ORDER_REFUND_REQUESTED, payload, propagate=True)


def publish_gov_order_status_update_requested(
    order_id: int, status: str, actor: dict, db: object = None
) -> Any:
    payload = {
        "event_id": _event_id(), "timestamp": _now_iso(),
        "order_id": order_id, "status": status, "actor": actor, "db": db,
    }
    logger.info("gov: order_status_update_requested order_id=%d status=%s", order_id, status)
    return publish(EVENT_GOV_ORDER_STATUS_UPDATE_REQUESTED, payload, propagate=True)


def publish_gov_order_tracking_update_requested(
    order_id: int, tracking_number: str, actor: dict, db: object = None
) -> Any:
    payload = {
        "event_id": _event_id(), "timestamp": _now_iso(),
        "order_id": order_id, "tracking_number": tracking_number, "actor": actor, "db": db,
    }
    logger.info("gov: order_tracking_update_requested order_id=%d", order_id)
    return publish(EVENT_GOV_ORDER_TRACKING_UPDATE_REQUESTED, payload, propagate=True)


def publish_gov_delete_bank_account_record_requested(
    kind: str, account_id: int, actor: dict, db: object = None
) -> Any:
    payload = {
        "event_id": _event_id(), "timestamp": _now_iso(),
        "kind": kind, "account_id": account_id, "actor": actor, "db": db,
    }
    logger.info("gov: delete_bank_account_record_requested kind=%s account_id=%d", kind, account_id)
    return publish(EVENT_GOV_DELETE_BANK_ACCOUNT_RECORD_REQUESTED, payload, propagate=True)


def publish_gov_entity_archive_requested(
    entity_type: str, entity_id: int, actor: dict, reason: Optional[str] = None, db: object = None,
) -> Any:
    payload = {
        "event_id": _event_id(), "timestamp": _now_iso(),
        "entity_type": entity_type, "entity_id": entity_id, "reason": reason, "actor": actor, "db": db,
    }
    logger.info("gov: entity_archive_requested %s id=%d", entity_type, entity_id)
    return publish(EVENT_GOV_ENTITY_ARCHIVE_REQUESTED, payload, propagate=True)


def publish_gov_entity_restore_requested(
    entity_type: str, entity_id: int, actor: dict, db: object = None
) -> Any:
    payload = {
        "event_id": _event_id(), "timestamp": _now_iso(),
        "entity_type": entity_type, "entity_id": entity_id, "actor": actor, "db": db,
    }
    logger.info("gov: entity_restore_requested %s id=%d", entity_type, entity_id)
    return publish(EVENT_GOV_ENTITY_RESTORE_REQUESTED, payload, propagate=True)


def publish_gov_bulk_archive_requested(
    entity_type: str, entity_ids: List[int], actor: dict, reason: Optional[str] = None, db: object = None,
) -> Any:
    payload = {
        "event_id": _event_id(), "timestamp": _now_iso(),
        "entity_type": entity_type, "entity_ids": entity_ids, "reason": reason, "actor": actor, "db": db,
    }
    logger.info("gov: bulk_archive_requested %s count=%d", entity_type, len(entity_ids))
    return publish(EVENT_GOV_BULK_ARCHIVE_REQUESTED, payload, propagate=True)


def publish_gov_bulk_restore_requested(
    entity_type: str, entity_ids: List[int], actor: dict, db: object = None
) -> Any:
    payload = {
        "event_id": _event_id(), "timestamp": _now_iso(),
        "entity_type": entity_type, "entity_ids": entity_ids, "actor": actor, "db": db,
    }
    logger.info("gov: bulk_restore_requested %s count=%d", entity_type, len(entity_ids))
    return publish(EVENT_GOV_BULK_RESTORE_REQUESTED, payload, propagate=True)


__all__ = [
    # event-type constants
    "EVENT_GOV_UPDATE_ROLE_PERMISSIONS_REQUESTED",
    "EVENT_GOV_BULK_DELETE_PRODUCTS_ADMIN_REQUESTED",
    "EVENT_GOV_BULK_PRODUCT_MODERATION_REQUESTED",
    "EVENT_GOV_DELETE_PRODUCT_ADMIN_REQUESTED",
    "EVENT_GOV_RESTORE_PRODUCT_ADMIN_REQUESTED",
    "EVENT_GOV_TOGGLE_PRODUCT_BADGE_REQUESTED",
    "EVENT_GOV_BULK_DELETE_USERS_ADMIN_REQUESTED",
    "EVENT_GOV_BULK_TOGGLE_USERS_ACTIVE_REQUESTED",
    "EVENT_GOV_BULK_UPDATE_USERS_ROLE_REQUESTED",
    "EVENT_GOV_TOGGLE_USER_ACTIVE_REQUESTED",
    "EVENT_GOV_UPDATE_USER_ROLE_REQUESTED",
    "EVENT_GOV_FORCE_RESET_PASSWORD_ADMIN_REQUESTED",
    "EVENT_GOV_BULK_UPDATE_STAFF_ACCOUNTS_REQUESTED",
    "EVENT_GOV_CREATE_STAFF_ACCOUNT_REQUESTED",
    "EVENT_GOV_DELETE_STAFF_ACCOUNT_REQUESTED",
    "EVENT_GOV_UPDATE_STAFF_ACCOUNT_REQUESTED",
    "EVENT_GOV_BULK_MANAGE_SUPPLIERS_REQUESTED",
    "EVENT_GOV_BULK_SUPPLIER_VERIFICATION_REQUESTED",
    "EVENT_GOV_VERIFY_SUPPLIER_REQUESTED",
    "EVENT_GOV_REJECT_SUPPLIER_REQUESTED",
    "EVENT_GOV_ORDER_BULK_DELETE_REQUESTED",
    "EVENT_GOV_ORDER_BULK_STATUS_UPDATE_REQUESTED",
    "EVENT_GOV_ORDER_DELETE_REQUESTED",
    "EVENT_GOV_ORDER_REFUND_REQUESTED",
    "EVENT_GOV_ORDER_STATUS_UPDATE_REQUESTED",
    "EVENT_GOV_ORDER_TRACKING_UPDATE_REQUESTED",
    "EVENT_GOV_DELETE_BANK_ACCOUNT_RECORD_REQUESTED",
    "EVENT_GOV_ENTITY_ARCHIVE_REQUESTED",
    "EVENT_GOV_ENTITY_RESTORE_REQUESTED",
    "EVENT_GOV_BULK_ARCHIVE_REQUESTED",
    "EVENT_GOV_BULK_RESTORE_REQUESTED",
    # publish functions
    "publish_gov_update_role_permissions_requested",
    "publish_gov_bulk_delete_products_admin_requested",
    "publish_gov_bulk_product_moderation_requested",
    "publish_gov_delete_product_admin_requested",
    "publish_gov_restore_product_admin_requested",
    "publish_gov_toggle_product_badge_requested",
    "publish_gov_bulk_delete_users_admin_requested",
    "publish_gov_bulk_toggle_users_active_requested",
    "publish_gov_bulk_update_users_role_requested",
    "publish_gov_toggle_user_active_requested",
    "publish_gov_update_user_role_requested",
    "publish_gov_force_reset_password_admin_requested",
    "publish_gov_bulk_update_staff_accounts_requested",
    "publish_gov_create_staff_account_requested",
    "publish_gov_delete_staff_account_requested",
    "publish_gov_update_staff_account_requested",
    "publish_gov_bulk_manage_suppliers_requested",
    "publish_gov_bulk_supplier_verification_requested",
    "publish_gov_verify_supplier_requested",
    "publish_gov_reject_supplier_requested",
    "publish_gov_order_bulk_delete_requested",
    "publish_gov_order_bulk_status_update_requested",
    "publish_gov_order_delete_requested",
    "publish_gov_order_refund_requested",
    "publish_gov_order_status_update_requested",
    "publish_gov_order_tracking_update_requested",
    "publish_gov_delete_bank_account_record_requested",
    "publish_gov_entity_archive_requested",
    "publish_gov_entity_restore_requested",
    "publish_gov_bulk_archive_requested",
    "publish_gov_bulk_restore_requested",
]


# === Merged from accounts/events.py ===

"""Accounts domain events.

Accounts is a *publishing* domain: when user-account state changes it emits
events that other domains may subscribe to (Law 3 — cross-domain writes only via
events). Events are plain dataclass-like objects; the bus is
``infrastructure.messaging.events.event_publisher.EventPublisher`` (which keys
listeners by event *type*).
"""


import uuid
from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class AccountsEvent:
    """Base class for all accounts domain events."""

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UserCreated(AccountsEvent):
    user_id: int = 0
    email: str = ""
    role: str = "customer"
    created_by: int | None = None


@dataclass
class UserRoleChanged(AccountsEvent):
    user_id: int = 0
    old_role: str = ""
    new_role: str = ""
    changed_by: int | None = None


@dataclass
class UserDeactivated(AccountsEvent):
    user_id: int = 0
    reason: str = ""
    deactivated_by: int | None = None


@dataclass
class UserActivated(AccountsEvent):
    user_id: int = 0
    activated_by: int | None = None


@dataclass
class UserDeleted(AccountsEvent):
    user_id: int = 0
    hard_delete: bool = False
    deleted_by: int | None = None


@dataclass
class PasswordChanged(AccountsEvent):
    user_id: int = 0
    self_initiated: bool = True


@dataclass
class PasswordForceReset(AccountsEvent):
    user_id: int = 0
    reset_by: int | None = None


@dataclass
class LoginSuccess(AccountsEvent):
    user_id: int = 0
    ip_address: str | None = None
    country_code: str | None = None


@dataclass
class LoginFailed(AccountsEvent):
    identifier: str = ""
    reason: str = ""
    ip_address: str | None = None


@dataclass
class TokenRevoked(AccountsEvent):
    user_id: int = 0
    jti: str = ""
    reason: str = ""


@dataclass
class MfaEnabled(AccountsEvent):
    user_id: int = 0


@dataclass
class MfaDisabled(AccountsEvent):
    user_id: int = 0


@dataclass
class SocialIdentityLinked(AccountsEvent):
    user_id: int = 0
    provider: str = ""
    provider_user_id: str = ""


@dataclass
class AddressBookChanged(AccountsEvent):
    user_id: int = 0
    action: str = ""
