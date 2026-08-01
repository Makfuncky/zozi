"""
Shared Audit Utilities — AuditAction constants + audit_log helper.

This is the single source of truth for audit logging. Both controllers and
services import from this module to avoid the services → controllers
forbidden dependency edge (DG violation).
"""
import json
import logging
import math
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, Optional, Union

from sqlalchemy.orm import Session

from models import AuditLog

logger = logging.getLogger(__name__)


class AuditAction:
    """All audit action constants — single source of truth."""
    LOGIN_SUCCESS = "LOGIN_SUCCESS"
    LOGIN_FAILED = "LOGIN_FAILED"
    LOGOUT = "LOGOUT"
    PASSWORD_RESET = "PASSWORD_RESET"
    EMAIL_VERIFIED = "EMAIL_VERIFIED"
    REGISTER = "REGISTER"
    TOKEN_REFRESH = "TOKEN_REFRESH"
    PRODUCT_UPLOAD = "PRODUCT_UPLOAD"
    PRODUCT_BULK_UPLOAD = "PRODUCT_BULK_UPLOAD"
    PRODUCT_UPDATE = "PRODUCT_UPDATE"
    PRODUCT_DELETE = "PRODUCT_DELETE"
    COUPON_CREATED = "COUPON_CREATED"
    COUPON_DELETED = "COUPON_DELETED"
    ADDRESS_CREATED = "ADDRESS_CREATED"
    ADDRESS_UPDATED = "ADDRESS_UPDATED"
    ADDRESS_DELETED = "ADDRESS_DELETED"
    ADDRESS_SET_DEFAULT = "ADDRESS_SET_DEFAULT"
    BANNER_CREATED = "BANNER_CREATED"
    BANNER_UPDATED = "BANNER_UPDATED"
    BANNER_DELETED = "BANNER_DELETED"
    BANNER_IMAGE_UPLOADED = "BANNER_IMAGE_UPLOADED"
    BANNER_REORDERED = "BANNER_REORDERED"
    FLASH_SALE_CREATED = "FLASH_SALE_CREATED"
    FLASH_SALE_UPDATED = "FLASH_SALE_UPDATED"
    FLASH_SALE_DELETED = "FLASH_SALE_DELETED"
    ORDER_CREATED = "ORDER_CREATED"
    ORDER_STATUS_CHANGED = "ORDER_STATUS_CHANGED"
    ORDER_STATUS_UPDATED = "ORDER_STATUS_UPDATED"
    ORDER_REFUNDED = "ORDER_REFUNDED"
    ORDER_DELETE = "ORDER_DELETE"
    SHIPMENT_STATUS_UPDATED = "SHIPMENT_STATUS_UPDATED"
    INVOICE_CREATED = "INVOICE_CREATED"
    INVOICE_STATUS_UPDATED = "INVOICE_STATUS_UPDATED"
    PAYOUT_REQUESTED = "PAYOUT_REQUESTED"
    PAYOUT_PROCESSED = "PAYOUT_PROCESSED"
    PAYOUT_VERIFIED = "PAYOUT_VERIFIED"
    PAYOUT_APPROVED = "PAYOUT_APPROVED"
    PAYOUT_REJECTED = "PAYOUT_REJECTED"
    MFA_ENABLED = "MFA_ENABLED"
    MFA_DISABLED = "MFA_DISABLED"
    MFA_ENFORCED = "MFA_ENFORCED"
    STAFF_UPDATED = "STAFF_UPDATED"
    STAFF_DELETED = "STAFF_DELETED"
    USER_TOGGLED_ACTIVE = "USER_TOGGLED_ACTIVE"
    BULK_USER_TOGGLE_ACTIVE = "BULK_USER_TOGGLE_ACTIVE"
    BULK_USER_ROLE_UPDATE = "BULK_USER_ROLE_UPDATE"
    FRAUD_FLAG = "FRAUD_FLAG"
    LOGISTICS_PARTNER_CREATED = "LOGISTICS_PARTNER_CREATED"
    COMMISSION_RATE_CHANGED = "COMMISSION_RATE_CHANGED"
    RETURN_REQUEST_CREATED = "RETURN_REQUEST_CREATED"
    RETURN_REQUEST_UPDATED = "RETURN_REQUEST_UPDATED"
    PROFILE_UPDATED = "PROFILE_UPDATED"
    PASSWORD_CHANGED = "PASSWORD_CHANGED"
    ROLE_CHANGED = "ROLE_CHANGED"
    STAFF_CREATED = "STAFF_CREATED"
    PRODUCT_MODERATED = "PRODUCT_MODERATED"
    SUPPLIER_VERIFIED = "SUPPLIER_VERIFIED"
    USER_DELETE = "USER_DELETE"
    PASSWORD_FORCE_RESET = "PASSWORD_FORCE_RESET"
    SUPPLIER_REJECTED = "SUPPLIER_REJECTED"
    ACCOUNT_LOCKED = "ACCOUNT_LOCKED"
    DATA_EXPORTED = "DATA_EXPORTED"
    ARCHIVE = "ARCHIVE"
    RESTORE = "RESTORE"
    BULK_ARCHIVE = "BULK_ARCHIVE"
    BULK_RESTORE = "BULK_RESTORE"
    PERMANENT_DELETE = "PERMANENT_DELETE"
    INBOX_RESET = "INBOX_RESET"

    # Financial / Treasury
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
    PERIOD_CLOSED = "PERIOD_CLOSED"
    REFUND_PROCESSED = "REFUND_PROCESSED"
    PAYROLL_PROCESSED = "PAYROLL_PROCESSED"
    EOSB_CALCULATED = "EOSB_CALCULATED"
    CASH_FORECAST_GENERATED = "CASH_FORECAST_GENERATED"
    FINANCIAL_SETTINGS_UPDATED = "FINANCIAL_SETTINGS_UPDATED"

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


def _json_default(value):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def audit_log(
    db: Session,
    action: str,
    user_id: Optional[int] = None,
    username: Optional[str] = None,
    user_role: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[Union[int, str]] = None,
    details: Optional[dict] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    status: str = "success",
) -> None:
    """Write an audit trail entry to the audit_logs table."""
    try:
        entry = AuditLog(
            user_id=user_id,
            username=username,
            user_role=user_role,
            action=action,
            entity_type=resource_type or "unknown",
            entity_id=int(resource_id) if isinstance(resource_id, (int, str)) and str(resource_id).isdigit() else None,
            details=json.dumps(details, default=_json_default) if details else None,
            ip_address=ip_address,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        db.add(entry)
        db.commit()
    except Exception as exc:
        logger.warning("audit_log write failed: %s", exc)
        try:
            db.rollback()
        except Exception:
            pass


def get_audit_logs(
    db: Session,
    page: int = 1,
    page_size: int = 50,
    action_filter: Optional[str] = None,
    user_id_filter: Optional[int] = None,
    resource_type_filter: Optional[str] = None,
    resource_id_filter: Optional[str] = None,
    status_filter: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    search: Optional[str] = None,
) -> dict:
    """Query audit logs with pagination and filters."""
    from sqlalchemy import or_

    query = db.query(AuditLog)

    if action_filter:
        query = query.filter(AuditLog.action == action_filter)
    if user_id_filter:
        query = query.filter(AuditLog.user_id == user_id_filter)
    if resource_type_filter:
        query = query.filter(AuditLog.entity_type == resource_type_filter)
    if resource_id_filter not in (None, ""):
        query = query.filter(AuditLog.entity_id == int(resource_id_filter) if resource_id_filter.isdigit() else None)
    if start_date:
        query = query.filter(AuditLog.created_at >= start_date)
    if end_date:
        query = query.filter(AuditLog.created_at <= end_date)
    if search:
        like = f"%{search}%"
        query = query.filter(
            or_(
                AuditLog.action.ilike(like),
                AuditLog.ip_address.ilike(like),
                AuditLog.details.ilike(like),
            )
        )

    total = query.count()
    items = (
        query.order_by(AuditLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": max(1, math.ceil(total / page_size)),
    }


def get_unique_actions(db: Session) -> list:
    """Return all distinct action values in the audit_logs table."""
    rows = db.query(AuditLog.action).distinct().order_by(AuditLog.action).all()
    return [r[0] for r in rows if r[0]]
