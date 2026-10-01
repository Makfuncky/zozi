"""Audit service for financial operations and compliance."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

from domains.audit.models.audit_schema_models import AuditLog


class AuditService:
    """Service for comprehensive audit logging of financial operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def log_action(
        self,
        user_id: Optional[int],
        action: str,
        resource_type: str,
        resource_id: Optional[str],
        details: Optional[dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        status: str = "success",
        country_code: Optional[str] = None,
    ) -> AuditLog:
        log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id else None,
            details=details and str(details) or None,
            ip_address=ip_address,
            user_agent=user_agent,
            status=status,
            country_code=country_code,
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log
    
    def log_financial_operation(
        self,
        user_id: int,
        operation: str,
        amount: float,
        currency: str,
        country_code: str,
        reference_id: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> AuditLog:
        return self.log_action(
            user_id=user_id,
            action=f"FINANCIAL_{operation}",
            resource_type="financial_transaction",
            resource_id=reference_id,
            details={
                "amount": amount,
                "currency": currency,
                "country_code": country_code,
                **(details or {}),
            },
            status="success",
        )
    
    def log_payroll_freeze(
        self,
        employee_id: int,
        reason: str,
        frozen_by: int,
    ) -> AuditLog:
        return self.log_action(
            user_id=frozen_by,
            action="PAYROLL_FREEZE",
            resource_type="employee",
            resource_id=str(employee_id),
            details={"reason": reason},
            status="success",
        )
    
    def log_coi_violation(
        self,
        employee_id: int,
        related_employee_id: int,
        entity_type: str,
        entity_id: int,
        blocked: bool = True,
    ) -> AuditLog:
        return self.log_action(
            user_id=None,
            action="COI_DETECTED",
            resource_type="conflict_of_interest",
            resource_id=str(employee_id),
            details={
                "related_employee_id": related_employee_id,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "blocked": blocked,
            },
            status="blocked" if blocked else "warning",
        )


def create_audit_service(db: Session) -> AuditService:
    return AuditService(db)



# === Merged from accounts/services/audit_service.py ===

class AuditAction:

    """Canonical catalogue of audit action names.



    Values are plain strings; the class is a namespace, not an enum, so that

    ``AuditAction.ANYTHING_NEW`` style additions stay cheap and callers can also

    pass raw strings.

    """



    # ── Generic CRUD / workflow (legacy domains.audit.services.logs.audit_service vocabulary) ─────────────

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
) -> AuditLog:
    """Write a single audit-log entry.

    Records an admin action against a resource, optionally capturing the
    before/after state for change tracking. Returns the persisted row.
    """
    log = AuditLog(
        user_id=user_id or actor_id,
        action=action,
        entity_type=resource_type or entity or "",
        entity_id=resource_id if isinstance(resource_id, int) else (
            int(entity_key) if isinstance(entity_key, int) else None
        ),
        username=username,
        user_role=user_role,
        details=details,
        ip_address=ip_address,
        country_code=country_code,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


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





