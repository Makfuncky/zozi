"""Canonical cross-cutting audit primitive.

This module is the **single** implementation of `AuditAction` / `audit_log`
for the whole backend. It lives in `utils/` because every layer
(`routers`, `controllers`, `services`, `jobs`, `events`) needs to record audit
events, and the circuit contract (ARCHITECTURE_DIAGRAM.md §10.2) allows every
layer to import `utils` while `utils` imports nothing above it.

Historically two divergent implementations existed:

* ``controllers/audit_controller.py`` — rich signature
  (``user_id`` / ``resource_type`` / ``resource_id`` / ``status``) used by ~200
  call sites. Importing it violated rule **W3** (mis-housed controller).
* ``utils/audit.py`` — narrow signature (``actor_id`` / ``entity`` /
  ``entity_key``). A previous refactor repointed dozens of call sites at this
  module *without* adapting the keyword arguments, so those calls raised
  ``TypeError`` at runtime and every audit trail silently died.

``audit_log`` below accepts **both** calling conventions so no call site can
break, and ``AuditAction`` carries the union of both catalogues.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, Optional, Union
from uuid import UUID

import structlog
from sqlalchemy.orm import Session

from _legacy.models.core import AuditLog
from utils.logging_config import get_request_id

logger = structlog.get_logger(__name__)

__all__ = ["AuditAction", "audit_log", "coerce_json_safe"]


class AuditAction:
    """Canonical catalogue of audit action names.

    Values are plain strings; the class is a namespace, not an enum, so that
    ``AuditAction.ANYTHING_NEW`` style additions stay cheap and callers can also
    pass raw strings.
    """

    # ── Generic CRUD / workflow (legacy utils.audit vocabulary) ─────────────
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    PUBLISH = "publish"
    ROLLBACK = "rollback"
    APPROVE = "approve"
    REJECT = "reject"
    CREATE_DRAFT = "create_draft"
    LOGIN = "login"
    EXPORT = "export"
    VIEW = "view"

    # ── Identity / session ──────────────────────────────────────────────────
    LOGIN_SUCCESS = "LOGIN_SUCCESS"
    LOGIN_FAILED = "LOGIN_FAILED"
    LOGOUT = "LOGOUT"
    PASSWORD_RESET = "PASSWORD_RESET"
    PASSWORD_CHANGED = "PASSWORD_CHANGED"
    PASSWORD_FORCE_RESET = "PASSWORD_FORCE_RESET"
    EMAIL_VERIFIED = "EMAIL_VERIFIED"
    REGISTER = "REGISTER"
    TOKEN_REFRESH = "TOKEN_REFRESH"
    ACCOUNT_LOCKED = "ACCOUNT_LOCKED"
    MFA_ENABLED = "MFA_ENABLED"
    MFA_DISABLED = "MFA_DISABLED"
    MFA_ENFORCED = "MFA_ENFORCED"
    PROFILE_UPDATED = "PROFILE_UPDATED"
    ROLE_CHANGED = "ROLE_CHANGED"

    # ── User / staff administration ─────────────────────────────────────────
    STAFF_CREATED = "STAFF_CREATED"
    STAFF_UPDATED = "STAFF_UPDATED"
    STAFF_DELETED = "STAFF_DELETED"
    USER_DELETE = "USER_DELETE"
    USER_TOGGLED_ACTIVE = "USER_TOGGLED_ACTIVE"
    BULK_USER_TOGGLE_ACTIVE = "BULK_USER_TOGGLE_ACTIVE"
    BULK_USER_ROLE_UPDATE = "BULK_USER_ROLE_UPDATE"

    # ── Permissions / IAM ───────────────────────────────────────────────────
    PERMISSION_GRANT = "PERMISSION_GRANT"
    PERMISSION_REVOKE = "PERMISSION_REVOKE"
    PERMISSION_APPROVE = "PERMISSION_APPROVE"
    PERMISSION_REJECT = "PERMISSION_REJECT"

    # ── Catalog ─────────────────────────────────────────────────────────────
    PRODUCT_UPLOAD = "PRODUCT_UPLOAD"
    PRODUCT_BULK_UPLOAD = "PRODUCT_BULK_UPLOAD"
    PRODUCT_UPDATE = "PRODUCT_UPDATE"
    PRODUCT_DELETE = "PRODUCT_DELETE"
    PRODUCT_MODERATED = "PRODUCT_MODERATED"

    # ── Marketing / promotions ──────────────────────────────────────────────
    COUPON_CREATED = "COUPON_CREATED"
    COUPON_DELETED = "COUPON_DELETED"
    BANNER_CREATED = "BANNER_CREATED"
    BANNER_UPDATED = "BANNER_UPDATED"
    BANNER_DELETED = "BANNER_DELETED"
    BANNER_IMAGE_UPLOADED = "BANNER_IMAGE_UPLOADED"
    BANNER_REORDERED = "BANNER_REORDERED"
    FLASH_SALE_CREATED = "FLASH_SALE_CREATED"
    FLASH_SALE_UPDATED = "FLASH_SALE_UPDATED"
    FLASH_SALE_DELETED = "FLASH_SALE_DELETED"

    # ── Customer data ───────────────────────────────────────────────────────
    ADDRESS_CREATED = "ADDRESS_CREATED"
    ADDRESS_UPDATED = "ADDRESS_UPDATED"
    ADDRESS_DELETED = "ADDRESS_DELETED"
    ADDRESS_SET_DEFAULT = "ADDRESS_SET_DEFAULT"

    # ── Orders / fulfilment ─────────────────────────────────────────────────
    ORDER_CREATED = "ORDER_CREATED"
    ORDER_STATUS_CHANGED = "ORDER_STATUS_CHANGED"
    ORDER_STATUS_UPDATED = "ORDER_STATUS_UPDATED"
    ORDER_REFUNDED = "ORDER_REFUNDED"
    ORDER_DELETE = "ORDER_DELETE"
    SHIPMENT_STATUS_UPDATED = "SHIPMENT_STATUS_UPDATED"
    RETURN_REQUEST_CREATED = "RETURN_REQUEST_CREATED"
    RETURN_REQUEST_UPDATED = "RETURN_REQUEST_UPDATED"

    # ── Supplier / logistics ────────────────────────────────────────────────
    SUPPLIER_VERIFIED = "SUPPLIER_VERIFIED"
    SUPPLIER_REJECTED = "SUPPLIER_REJECTED"
    LOGISTICS_PARTNER_CREATED = "LOGISTICS_PARTNER_CREATED"
    COMMISSION_RATE_CHANGED = "COMMISSION_RATE_CHANGED"

    # ── Finance / treasury ──────────────────────────────────────────────────
    INVOICE_CREATED = "INVOICE_CREATED"
    INVOICE_STATUS_UPDATED = "INVOICE_STATUS_UPDATED"
    PAYOUT_REQUESTED = "PAYOUT_REQUESTED"
    PAYOUT_PROCESSED = "PAYOUT_PROCESSED"
    PAYOUT_VERIFIED = "PAYOUT_VERIFIED"
    PAYOUT_APPROVED = "PAYOUT_APPROVED"
    PAYOUT_REJECTED = "PAYOUT_REJECTED"
    JOURNAL_ENTRY_CREATED = "JOURNAL_ENTRY_CREATED"
    JOURNAL_ENTRY_APPROVED = "JOURNAL_ENTRY_APPROVED"
    JOURNAL_ENTRY_REJECTED = "JOURNAL_ENTRY_REJECTED"
    TREASURY_TRANSACTION_CREATED = "TREASURY_TRANSACTION_CREATED"
    CASH_TRANSACTION_CREATED = "CASH_TRANSACTION_CREATED"
    VAT_REMITTANCE_CREATED = "VAT_REMITTANCE_CREATED"
    BANK_TRANSACTION_CREATED = "BANK_TRANSACTION_CREATED"
    BANK_TRANSACTION_RECONCILED = "BANK_TRANSACTION_RECONCILED"
    BANK_TRANSACTION_FLAGGED = "BANK_TRANSACTION_FLAGGED"
    ACCOUNT_CREATED = "ACCOUNT_CREATED"
    ACCOUNT_GROUP_CREATED = "ACCOUNT_GROUP_CREATED"
    CHART_OF_ACCOUNTS_SEEDED = "CHART_OF_ACCOUNTS_SEEDED"
    TRIAL_BALANCE_VIEWED = "TRIAL_BALANCE_VIEWED"
    FINANCIAL_REPORT_GENERATED = "FINANCIAL_REPORT_GENERATED"
    FINANCIAL_SETTINGS_UPDATED = "FINANCIAL_SETTINGS_UPDATED"
    PERIOD_CLOSED = "PERIOD_CLOSED"
    REFUND_PROCESSED = "REFUND_PROCESSED"
    PAYROLL_PROCESSED = "PAYROLL_PROCESSED"
    EOSB_CALCULATED = "EOSB_CALCULATED"
    CASH_FORECAST_GENERATED = "CASH_FORECAST_GENERATED"

    # ── Risk / compliance / lifecycle ───────────────────────────────────────
    FRAUD_FLAG = "FRAUD_FLAG"
    DATA_EXPORTED = "DATA_EXPORTED"
    ARCHIVE = "ARCHIVE"
    RESTORE = "RESTORE"
    BULK_ARCHIVE = "BULK_ARCHIVE"
    BULK_RESTORE = "BULK_RESTORE"
    PERMANENT_DELETE = "PERMANENT_DELETE"
    INBOX_RESET = "INBOX_RESET"

    @classmethod
    def get_archive_action(cls, entity_name: str) -> str:
        return f"{entity_name.upper()}_ARCHIVE"

    @classmethod
    def get_restore_action(cls, entity_name: str) -> str:
        return f"{entity_name.upper()}_RESTORE"

    @classmethod
    def get_bulk_archive_action(cls, entity_name: str) -> str:
        return f"BULK_{entity_name.upper()}_ARCHIVE"

    @classmethod
    def get_bulk_restore_action(cls, entity_name: str) -> str:
        return f"BULK_{entity_name.upper()}_RESTORE"


def coerce_json_safe(value: Any) -> Any:
    """Recursively convert `value` into something a JSON column accepts."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Enum):
        return coerce_json_safe(value.value)
    if isinstance(value, dict):
        return {str(k): coerce_json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [coerce_json_safe(v) for v in value]
    return str(value)


def _as_entity_id(raw: Any) -> Optional[int]:
    if raw is None or isinstance(raw, bool):
        return None
    if isinstance(raw, int):
        return raw
    text = str(raw).strip()
    if text.isdigit() or (text.startswith("-") and text[1:].isdigit()):
        try:
            return int(text)
        except ValueError:
            return None
    return None


def audit_log(
    db: Session,
    action: str = "",
    user_id: Optional[int] = None,
    username: Optional[str] = None,
    user_role: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[Union[int, str]] = None,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    status: str = "success",
    *,
    actor_id: Optional[int] = None,
    entity: Optional[str] = None,
    entity_key: Optional[Union[int, str]] = None,
    before: Optional[Dict[str, Any]] = None,
    after: Optional[Dict[str, Any]] = None,
    country_code: Optional[str] = None,
) -> bool:
    """Persist one audit event. Never raises.

    Two equivalent calling conventions are supported:

    ``audit_log(db, action=..., user_id=..., resource_type=..., resource_id=...)``
    ``audit_log(db, action=..., actor_id=..., entity=..., entity_key=...)``

    Returns ``True`` when the row was committed, ``False`` otherwise. Failures
    are logged and swallowed: auditing must never break the business flow.
    """
    effective_user_id = user_id if user_id is not None else actor_id
    if effective_user_id is not None and effective_user_id <= 0:
        effective_user_id = None
    effective_type = resource_type or entity or "unknown"
    effective_key = resource_id if resource_id is not None else entity_key

    payload: Dict[str, Any] = {}
    if before is not None:
        payload["before"] = coerce_json_safe(before)
    if after is not None:
        payload["after"] = coerce_json_safe(after)
    if details:
        payload.update(coerce_json_safe(details))
    if status and status != "success":
        payload.setdefault("status", status)
    entity_id = _as_entity_id(effective_key)
    if entity_id is None and effective_key not in (None, ""):
        # Preserve non-numeric identifiers (uuid / slug) instead of dropping them.
        payload.setdefault("resource_id", str(effective_key))
    if user_agent:
        payload.setdefault("user_agent", user_agent)
    if country_code:
        payload.setdefault("country_code", country_code)
    request_id = get_request_id()
    if request_id:
        payload.setdefault("request_id", request_id)

    try:
        entry = AuditLog(
            action=action or AuditAction.UPDATE,
            entity_type=effective_type,
            entity_id=entity_id,
            user_id=effective_user_id,
            username=username or (details or {}).get("username"),
            user_role=user_role or (details or {}).get("role"),
            details=payload or None,
            ip_address=ip_address,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        db.add(entry)
        db.commit()
        return True
    except Exception as exc:  # pragma: no cover - defensive, audit must not raise
        logger.warning(
            "audit_log_failed",
            action=action,
            entity=effective_type,
            error=str(exc),
        )
        try:
            db.rollback()
        except Exception:
            pass
        return False
