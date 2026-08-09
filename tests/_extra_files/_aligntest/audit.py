"""
Audit logging utility
Persists audit events to the audit_logs table.

The signature is intentionally tolerant: it accepts both the service-style
calls introduced by the write services (``actor_id``, ``entity``,
``entity_key``, ``before``, ``after``) and the controller-style calls used
across the codebase (``user_id``, ``username``, ``user_role``,
``resource_type``, ``resource_id``, ``status``). This keeps the existing
~115 controller call sites working without mass refactoring while still
supporting the newer service-layer semantics.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

import structlog
from sqlalchemy.orm import Session

from data.models_core import AuditLog
from utils.logging_config import get_request_id

logger = structlog.get_logger(__name__)


class AuditAction(str):
    """Enumeration of audit action names.

    Values are stable snake_case strings stored in the ``action`` column.
    Both the original controller-set members and the service-layer members
    are present so no caller raises ``AttributeError``.
    """

    # ── Base / lifecycle ────────────────────────────────────────────────────
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    ARCHIVE = "archive"
    RESTORE = "restore"
    PERMANENT_DELETE = "permanent_delete"
    BULK_ARCHIVE = "bulk_archive"
    BULK_RESTORE = "bulk_restore"
    PUBLISH = "publish"
    ROLLBACK = "rollback"
    APPROVE = "approve"
    REJECT = "reject"
    CREATE_DRAFT = "create_draft"
    LOGIN = "login"
    LOGOUT = "logout"
    EXPORT = "export"
    VIEW = "view"

    # ── Auth / account ──────────────────────────────────────────────────────
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT_FAILED = "logout_failed"
    ACCOUNT_LOCKED = "account_locked"
    PROFILE_UPDATED = "profile_updated"
    PASSWORD_FORCE_RESET = "password_force_reset"
    PASSWORD_CHANGE = "password_change"
    PASSWORD_RESET = "password_reset"

    # ── Users / roles / staff ───────────────────────────────────────────────
    USER_CREATE = "user_create"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"
    USER_ROLE_CHANGE = "user_role_change"
    ROLE_CHANGED = "role_changed"
    STAFF_CREATED = "staff_created"

    # ── Products ────────────────────────────────────────────────────────────
    PRODUCT_CREATE = "product_create"
    PRODUCT_UPDATE = "product_update"
    PRODUCT_DELETE = "product_delete"
    PRODUCT_UPLOAD = "product_upload"
    PRODUCT_STOCK_UPDATED = "product_stock_updated"

    # ── Orders ──────────────────────────────────────────────────────────────
    ORDER_CREATE = "order_create"
    ORDER_CREATED = "order_created"
    ORDER_UPDATE = "order_update"
    ORDER_DELETE = "order_delete"
    ORDER_STATUS_CHANGE = "order_status_change"
    ORDER_STATUS_CHANGED = "order_status_changed"
    ORDER_REFUNDED = "order_refunded"

    # ── Invoices ────────────────────────────────────────────────────────────
    INVOICE_CREATE = "invoice_create"
    INVOICE_CREATED = "invoice_created"
    INVOICE_UPDATE = "invoice_update"
    INVOICE_DELETE = "invoice_delete"
    INVOICE_STATUS_UPDATED = "invoice_status_updated"

    # ── Commission / payments ───────────────────────────────────────────────
    COMMISSION_UPDATE = "commission_update"
    COMMISSION_CATEGORY_RATE_UPDATED = "commission_category_rate_updated"
    COMMISSION_BADGE_TIER_UPDATED = "commission_badge_tier_updated"
    PAYMENT_CREATE = "payment_create"
    PAYMENT_UPDATE = "payment_update"
    PAYMENT_CAPTURE = "payment_capture"
    PAYMENT_REFUND = "payment_refund"
    REFUND_ISSUED = "refund_issued"
    PAYOUT_REQUESTED = "payout_requested"
    PAYOUT_PROCESSED = "payout_processed"

    # ── Shipments / logistics ───────────────────────────────────────────────
    SHIPMENT_CREATE = "shipment_create"
    SHIPMENT_UPDATE = "shipment_update"
    SHIPMENT_DELIVERED = "shipment_delivered"
    SHIPMENT_STATUS_UPDATED = "shipment_status_updated"

    # ── Returns ──────────────────────────────────────────────────────────────
    RETURN_REQUEST_CREATE = "return_request_create"
    RETURN_REQUEST_CREATED = "return_request_created"
    RETURN_REQUEST_UPDATE = "return_request_update"
    RETURN_REQUEST_UPDATED = "return_request_updated"
    RETURN_REQUEST_APPROVE = "return_request_approve"
    RETURN_REQUEST_REJECT = "return_request_reject"

    # ── Permissions ─────────────────────────────────────────────────────────
    PERMISSION_GRANT = "permission_grant"
    PERMISSION_REVOKE = "permission_revoke"
    PERMISSION_APPROVE = "permission_approve"
    PERMISSION_REJECT = "permission_reject"

    # ── Config / settings ───────────────────────────────────────────────────
    CONFIG_CHANGE = "config_change"

    # ── Suppliers / badges ───────────────────────────────────────────────────
    SUPPLIER_APPROVE = "supplier_approve"
    SUPPLIER_REJECT = "supplier_reject"
    SUPPLIER_VERIFIED = "supplier_verified"
    SUPPLIER_REJECTED = "supplier_rejected"
    BADGE_ASSIGN = "badge_assign"
    BADGE_REVOKE = "badge_revoke"

    # ── Settlement ───────────────────────────────────────────────────────────
    SETTLEMENT_CREATE = "settlement_create"
    SETTLEMENT_PROCESS = "settlement_process"

    # ── Banners / flash sales / addresses ────────────────────────────────────
    BANNER_CREATED = "banner_created"
    BANNER_UPDATED = "banner_updated"
    BANNER_DELETED = "banner_deleted"
    BANNER_IMAGE_UPLOADED = "banner_image_uploaded"
    BANNER_REORDERED = "banner_reordered"
    FLASH_SALE_CREATED = "flash_sale_created"
    FLASH_SALE_UPDATED = "flash_sale_updated"
    FLASH_SALE_DELETED = "flash_sale_deleted"
    ADDRESS_CREATED = "address_created"
    ADDRESS_UPDATED = "address_updated"
    ADDRESS_DELETED = "address_deleted"
    ADDRESS_SET_DEFAULT = "address_set_default"

    # ── Finance / accounting ─────────────────────────────────────────────────
    CHART_OF_ACCOUNTS_SEEDED = "chart_of_accounts_seeded"
    JOURNAL_ENTRY_CREATED = "journal_entry_created"
    BANK_TRANSACTION_RECONCILED = "bank_transaction_reconciled"
    FINANCIAL_REPORT_GENERATED = "financial_report_generated"
    CASH_FORECAST_GENERATED = "cash_forecast_generated"
    PERIOD_CLOSED = "period_closed"
    TRIAL_BALANCE_VIEWED = "trial_balance_viewed"
    TREASURY_TRANSACTION_CREATED = "treasury_transaction_created"
    DATA_EXPORTED = "data_exported"
    INBOX_RESET = "inbox_reset"


# Actions whose audit record is critical enough that a logging failure must
# surface (raise) rather than be silently swallowed. These are delete/restore
# class operations where a missing audit trail is a real integrity problem.
_DELETE_CLASS_ACTIONS = frozenset(
    {
        AuditAction.DELETE,
        AuditAction.ARCHIVE,
        AuditAction.RESTORE,
        AuditAction.PERMANENT_DELETE,
        AuditAction.BULK_ARCHIVE,
        AuditAction.BULK_RESTORE,
        "delete",
        "archive",
        "restore",
        "permanent_delete",
        "bulk_archive",
        "bulk_restore",
    }
)


def _resolve_actor_id(actor_id: Any, user_id: Any) -> Optional[int]:
    """Return an integer actor id, preferring ``actor_id`` then ``user_id``."""
    if isinstance(actor_id, int):
        return actor_id
    if isinstance(user_id, int):
        return user_id
    return None


def audit_log(
    db: Session,
    actor_id: Optional[int] = None,
    action: Optional[str] = None,
    entity: Optional[str] = None,
    entity_key: Optional[Any] = None,
    before: Optional[Any] = None,
    after: Optional[Any] = None,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    # controller-style aliases
    user_id: Optional[int] = None,
    username: Optional[str] = None,
    user_role: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[Any] = None,
    status: Optional[str] = None,
    **kwargs: Any,
) -> bool:
    """Persist an audit entry.

    Accepts both service-style and controller-style call shapes. Returns
    ``True`` on success, ``False`` when the entry could not be written for a
    non-critical action. For delete-class actions a write failure is raised
    instead of swallowed.
    """
    if action is None:
        logger.error("audit_log_missing_action")
        return False

    details = details or {}

    resolved_actor = _resolve_actor_id(actor_id, user_id)
    user_id_value = resolved_actor if (isinstance(resolved_actor, int) and resolved_actor > 0) else None

    ent_type = entity or resource_type or details.get("entity_type") or ""
    raw_key = entity_key if entity_key is not None else resource_id
    if raw_key is not None and str(raw_key).isdigit():
        ent_id: Optional[int] = int(raw_key)
    else:
        ent_id = None

    uname = username or details.get("username")
    urole = user_role or details.get("role")
    actor_label = uname or details.get("actor")

    merged_details: Dict[str, Any] = {
        "before": before,
        "after": after,
        **details,
        "request_id": get_request_id(),
    }
    if status is not None:
        merged_details["status"] = status

    try:
        entry = AuditLog(
            action=action,
            entity_type=ent_type if ent_type else "unknown",
            entity_id=ent_id,
            user_id=user_id_value,
            username=uname,
            user_role=urole,
            actor=actor_label,
            old_value_json=before,
            new_value_json=after,
            details=merged_details,
            ip_address=ip_address,
            country_code=details.get("country_code"),
        )
        db.add(entry)
        db.commit()
        return True
    except Exception as exc:
        logger.error("audit_log_failed", action=action, entity=ent_type, error=str(exc))
        try:
            db.rollback()
        except Exception:
            pass
        if action in _DELETE_CLASS_ACTIONS:
            raise
        return False
