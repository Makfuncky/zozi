"""Sub-Ledger Service — per-customer (AR) and per-supplier (AP) tracking.

Bridges GL account balances to entity-level outstanding amounts.
Allows drill-down from GL account 1030 (AR) and 2010 (AP) to individual
customer/supplier sub-ledger entries.
"""
from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from data.models import (
    ARLedgerEntry,
    APLedger,
    Account,
    AccountBalance,
    Invoice,
    SupplierSettlement,
    Order,
    User,
)
from data.models_treasury_finance import APLedger as _APLedger
from utils.money import round_money

logger = logging.getLogger(__name__)


# ── AR (Accounts Receivable) Sub-Ledger ────────────────────────────────────


def post_ar_invoice(
    db: Session,
    customer_id: int,
    amount: Decimal,
    order_id: Optional[int] = None,
    invoice_id: Optional[int] = None,
    due_date: Optional[datetime] = None,
    description: Optional[str] = None,
    currency: str = "OMR",
    country_code: Optional[str] = None,
    created_by: Optional[int] = None,
) -> ARLedgerEntry:
    """Post an invoice to the AR sub-ledger (customer owes money)."""
    current_balance = _get_ar_balance(db, customer_id, currency)
    entry = ARLedgerEntry(
        customer_id=customer_id,
        order_id=order_id,
        invoice_id=invoice_id,
        reference_type="invoice" if invoice_id else "order",
        reference_id=invoice_id or order_id,
        entry_type="invoice",
        amount=amount,
        balance_after=round_money(current_balance + amount),
        currency=currency,
        status="open",
        due_date=due_date,
        description=description or f"Invoice for customer #{customer_id}",
        created_by=created_by,
        country_code=country_code,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def post_ar_payment(
    db: Session,
    customer_id: int,
    amount: Decimal,
    invoice_id: Optional[int] = None,
    order_id: Optional[int] = None,
    description: Optional[str] = None,
    currency: str = "OMR",
    country_code: Optional[str] = None,
    created_by: Optional[int] = None,
) -> ARLedgerEntry:
    """Post a payment to the AR sub-ledger (customer paid)."""
    current_balance = _get_ar_balance(db, customer_id, currency)
    entry = ARLedgerEntry(
        customer_id=customer_id,
        order_id=order_id,
        invoice_id=invoice_id,
        reference_type="payment",
        reference_id=invoice_id or order_id,
        entry_type="payment",
        amount=amount,
        balance_after=round_money(current_balance - amount),
        currency=currency,
        status="paid",
        settled_at=datetime.utcnow(),
        description=description or f"Payment from customer #{customer_id}",
        created_by=created_by,
        country_code=country_code,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)

    # Update related invoice status if provided
    if invoice_id:
        _update_ar_invoice_status(db, invoice_id)
    return entry


def get_ar_summary(
    db: Session,
    customer_id: Optional[int] = None,
    status: Optional[str] = None,
    country_code: Optional[str] = None,
    limit: int = 50,
) -> dict:
    """Get AR sub-ledger summary with outstanding balance."""
    q = db.query(ARLedgerEntry).filter(ARLedgerEntry.is_deleted == False)
    if customer_id:
        q = q.filter(ARLedgerEntry.customer_id == customer_id)
    if status:
        q = q.filter(ARLedgerEntry.status == status)
    if country_code:
        q = q.filter(ARLedgerEntry.country_code == country_code)

    entries = q.order_by(ARLedgerEntry.created_at.desc()).limit(limit).all()

    total_outstanding = db.query(
        func.coalesce(func.sum(ARLedgerEntry.amount).filter(ARLedgerEntry.status.in_(["open", "partially_paid"])), 0)
    ).filter(ARLedgerEntry.is_deleted == False).scalar() or Decimal("0.00")

    return {
        "total_outstanding": float(total_outstanding),
        "entry_count": len(entries),
        "entries": [
            {
                "id": e.id,
                "customer_id": e.customer_id,
                "entry_type": e.entry_type,
                "amount": float(e.amount),
                "balance_after": float(e.balance_after) if e.balance_after else None,
                "currency": e.currency,
                "status": e.status,
                "due_date": e.due_date.isoformat() if e.due_date else None,
                "created_at": e.created_at.isoformat(),
                "description": e.description,
            }
            for e in entries
        ],
    }


def _get_ar_balance(db: Session, customer_id: int, currency: str) -> Decimal:
    result = db.query(
        func.coalesce(
            func.sum(ARLedgerEntry.amount).filter(ARLedgerEntry.entry_type == "invoice"),
            0,
        ) -
        func.coalesce(
            func.sum(ARLedgerEntry.amount).filter(ARLedgerEntry.entry_type == "payment"),
            0,
        )
    ).filter(
        ARLedgerEntry.customer_id == customer_id,
        ARLedgerEntry.currency == currency,
        ARLedgerEntry.is_deleted == False,
        ARLedgerEntry.status != "written_off",
    ).scalar()
    return result or Decimal("0.00")


def _update_ar_invoice_status(db: Session, invoice_id: int) -> None:
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        return
    total_paid = db.query(
        func.coalesce(func.sum(ARLedgerEntry.amount), 0)
    ).filter(
        ARLedgerEntry.invoice_id == invoice_id,
        ARLedgerEntry.entry_type == "payment",
        ARLedgerEntry.is_deleted == False,
    ).scalar() or Decimal("0.00")

    if total_paid >= (invoice.total_amount or Decimal("0.00")):
        invoice.status = "paid"
        # Update AR entries
        db.query(ARLedgerEntry).filter(
            ARLedgerEntry.invoice_id == invoice_id,
            ARLedgerEntry.entry_type == "invoice",
        ).update({"status": "paid", "settled_at": datetime.utcnow()})
        db.commit()


# ── AP (Accounts Payable) Sub-Ledger ───────────────────────────────────────


def post_ap_payable(
    db: Session,
    supplier_id: int,
    amount: Decimal,
    order_id: Optional[int] = None,
    invoice_id: Optional[int] = None,
    settlement_id: Optional[int] = None,
    due_date: Optional[datetime] = None,
    description: Optional[str] = None,
    currency: str = "OMR",
    country_code: Optional[str] = None,
    created_by: Optional[int] = None,
) -> APLedger:
    """Post a supplier payable (we owe supplier money)."""
    current_balance = _get_ap_balance(db, supplier_id, currency)
    entry = APLedger(
        supplier_id=supplier_id,
        order_id=order_id,
        invoice_id=invoice_id,
        settlement_id=settlement_id,
        reference_type="settlement" if settlement_id else "invoice",
        reference_id=settlement_id or invoice_id or order_id,
        entry_type="payable",
        amount=amount,
        balance_after=round_money(current_balance + amount),
        currency=currency,
        status="open",
        due_date=due_date,
        description=description or f"Payable to supplier #{supplier_id}",
        created_by=created_by,
        country_code=country_code,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def post_ap_payment(
    db: Session,
    supplier_id: int,
    amount: Decimal,
    settlement_id: Optional[int] = None,
    invoice_id: Optional[int] = None,
    description: Optional[str] = None,
    currency: str = "OMR",
    country_code: Optional[str] = None,
    created_by: Optional[int] = None,
) -> APLedger:
    """Record a payment to a supplier (we paid)."""
    current_balance = _get_ap_balance(db, supplier_id, currency)
    entry = APLedger(
        supplier_id=supplier_id,
        settlement_id=settlement_id,
        invoice_id=invoice_id,
        reference_type="payment",
        reference_id=settlement_id or invoice_id,
        entry_type="payment",
        amount=amount,
        balance_after=round_money(current_balance - amount),
        currency=currency,
        status="closed",
        paid_at=datetime.utcnow(),
        description=description or f"Payment to supplier #{supplier_id}",
        created_by=created_by,
        country_code=country_code,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)

    if settlement_id:
        db.query(SupplierSettlement).filter(
            SupplierSettlement.id == settlement_id
        ).update({"status": "paid", "settled_at": datetime.utcnow()})
        db.commit()
    return entry


def get_ap_summary(
    db: Session,
    supplier_id: Optional[int] = None,
    status: Optional[str] = None,
    country_code: Optional[str] = None,
    limit: int = 50,
) -> dict:
    """Get AP sub-ledger with outstanding balance."""
    q = db.query(APLedger).filter(APLedger.is_deleted == False)
    if supplier_id:
        q = q.filter(APLedger.supplier_id == supplier_id)
    if status:
        q = q.filter(APLedger.status == status)
    if country_code:
        q = q.filter(APLedger.country_code == country_code)

    entries = q.order_by(APLedger.created_at.desc()).limit(limit).all()

    total_outstanding = db.query(
        func.coalesce(func.sum(APLedger.amount).filter(APLedger.status.in_(["open", "partially_paid"])), 0)
    ).filter(APLedger.is_deleted == False).scalar() or Decimal("0.00")

    return {
        "total_outstanding": float(total_outstanding),
        "entry_count": len(entries),
        "entries": [
            {
                "id": e.id,
                "supplier_id": e.supplier_id,
                "entry_type": e.entry_type,
                "amount": float(e.amount),
                "balance_after": float(e.balance_after) if e.balance_after else None,
                "currency": e.currency,
                "status": e.status,
                "due_date": e.due_date.isoformat() if e.due_date else None,
                "paid_at": e.paid_at.isoformat() if e.paid_at else None,
                "created_at": e.created_at.isoformat(),
                "description": e.description,
            }
            for e in entries
        ],
    }


def _get_ap_balance(db: Session, supplier_id: int, currency: str) -> Decimal:
    result = db.query(
        func.coalesce(
            func.sum(APLedger.amount).filter(APLedger.entry_type == "payable"),
            0,
        ) -
        func.coalesce(
            func.sum(APLedger.amount).filter(APLedger.entry_type == "payment"),
            0,
        )
    ).filter(
        APLedger.supplier_id == supplier_id,
        APLedger.currency == currency,
        APLedger.is_deleted == False,
        APLedger.status != "disputed",
    ).scalar()
    return result or Decimal("0.00")
