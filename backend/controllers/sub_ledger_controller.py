"""Sub-Ledger Controller — AR/AP endpoints for the accounting router."""
from __future__ import annotations

import logging
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session
from fastapi import HTTPException

from services.sub_ledger_service import (
    get_ar_summary,
    post_ar_invoice,
    post_ar_payment,
    get_ap_summary,
    post_ap_payable,
    post_ap_payment,
)
from controllers.audit_controller import AuditAction, audit_log

logger = logging.getLogger(__name__)


def controller_get_ar_summary(
    db: Session,
    customer_id: Optional[int] = None,
    status: Optional[str] = None,
    country_code: Optional[str] = None,
    limit: int = 50,
) -> dict:
    return get_ar_summary(db, customer_id=customer_id, status=status, country_code=country_code, limit=limit)


def controller_get_ap_summary(
    db: Session,
    supplier_id: Optional[int] = None,
    status: Optional[str] = None,
    country_code: Optional[str] = None,
    limit: int = 50,
) -> dict:
    return get_ap_summary(db, supplier_id=supplier_id, status=status, country_code=country_code, limit=limit)


def controller_post_ar_invoice(
    db: Session,
    customer_id: int,
    amount: float,
    order_id: Optional[int] = None,
    invoice_id: Optional[int] = None,
    due_date: Optional[str] = None,
    description: Optional[str] = None,
    currency: str = "OMR",
    country_code: Optional[str] = None,
    admin_user: Optional[dict] = None,
) -> dict:
    import datetime as dt
    due = dt.datetime.fromisoformat(due_date) if due_date else None
    entry = post_ar_invoice(
        db, customer_id=customer_id, amount=Decimal(str(amount)),
        order_id=order_id, invoice_id=invoice_id, due_date=due,
        description=description, currency=currency, country_code=country_code,
        created_by=admin_user.get("id") if admin_user else None,
    )
    audit_log(
        db=db, action=AuditAction.JOURNAL_ENTRY_CREATED,
        user_id=admin_user.get("id") if admin_user else None,
        username=admin_user.get("username") if admin_user else None,
        user_role=admin_user.get("role") if admin_user else None,
        resource_type="ar_invoice", resource_id=entry.id,
        details={"customer_id": customer_id, "amount": amount, "currency": currency},
    )
    return {"id": entry.id, "status": entry.status, "balance_after": float(entry.balance_after or 0)}


def controller_post_ar_payment(
    db: Session,
    customer_id: int,
    amount: float,
    invoice_id: Optional[int] = None,
    order_id: Optional[int] = None,
    description: Optional[str] = None,
    currency: str = "OMR",
    country_code: Optional[str] = None,
    admin_user: Optional[dict] = None,
) -> dict:
    entry = post_ar_payment(
        db, customer_id=customer_id, amount=Decimal(str(amount)),
        invoice_id=invoice_id, order_id=order_id,
        description=description, currency=currency, country_code=country_code,
        created_by=admin_user.get("id") if admin_user else None,
    )
    audit_log(
        db=db, action=AuditAction.BANK_TRANSACTION_RECONCILED,
        user_id=admin_user.get("id") if admin_user else None,
        username=admin_user.get("username") if admin_user else None,
        user_role=admin_user.get("role") if admin_user else None,
        resource_type="ar_payment", resource_id=entry.id,
        details={"customer_id": customer_id, "amount": amount, "currency": currency},
    )
    return {"id": entry.id, "status": entry.status, "balance_after": float(entry.balance_after or 0)}


def controller_post_ap_payable(
    db: Session,
    supplier_id: int,
    amount: float,
    order_id: Optional[int] = None,
    settlement_id: Optional[int] = None,
    due_date: Optional[str] = None,
    description: Optional[str] = None,
    currency: str = "OMR",
    country_code: Optional[str] = None,
    admin_user: Optional[dict] = None,
) -> dict:
    import datetime as dt
    due = dt.datetime.fromisoformat(due_date) if due_date else None
    entry = post_ap_payable(
        db, supplier_id=supplier_id, amount=Decimal(str(amount)),
        order_id=order_id, settlement_id=settlement_id, due_date=due,
        description=description, currency=currency, country_code=country_code,
        created_by=admin_user.get("id") if admin_user else None,
    )
    return {"id": entry.id, "status": entry.status, "balance_after": float(entry.balance_after or 0)}


def controller_post_ap_payment(
    db: Session,
    supplier_id: int,
    amount: float,
    settlement_id: Optional[int] = None,
    description: Optional[str] = None,
    currency: str = "OMR",
    country_code: Optional[str] = None,
    admin_user: Optional[dict] = None,
) -> dict:
    entry = post_ap_payment(
        db, supplier_id=supplier_id, amount=Decimal(str(amount)),
        settlement_id=settlement_id,
        description=description, currency=currency, country_code=country_code,
        created_by=admin_user.get("id") if admin_user else None,
    )
    return {"id": entry.id, "status": entry.status, "balance_after": float(entry.balance_after or 0)}
