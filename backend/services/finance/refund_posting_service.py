"""
Refund Posting Service — Auto journal entry creation on refund approval.

Handles:
  - #26: Auto Refund Posting + Supplier Deduction
  
Refund Journal Entries:
  - Card refund: Dr 2030 Customer Refund Reserve / Cr 1020 Gateway Clearing
  - COD refund: Dr 2030 Customer Refund Reserve / Cr 1010 Cash Operating
  - Commission reversal: Dr 4010 Commission Revenue / Cr 2030 Customer Refund Reserve
  - VAT reversal: Dr 2040 VAT Payable / Cr 2030 Customer Refund Reserve
  - Supplier deduction: Dr 2010 Supplier Payable / Cr 2030 Customer Refund Reserve
"""
from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from models import (
    RefundLedger,
    Order,
    SupplierSettlement,
    TransactionLedger,
    FinanceAutomationLog,
    FinanceAuditLog,
)
from db.schemas import JournalEntryCreate, JournalLineInput
from services import general_ledger_service as gl
from utils.datetime_utils import utcnow as _utcnow

logger = logging.getLogger(__name__)


# ── #26: Auto Refund Posting ───────────────────────────────────────────────


def post_refund_automatically(
    db: Session,
    refund_id: int,
    approved_by: int = None,
    country_code: str = None,
) -> dict:
    """
    Auto-post journal entries when a refund is approved.
    
    Creates reversing entries:
    1. Reverse original revenue recognition
    2. Post refund liability
    3. Deduct from supplier payable (if applicable)
    """
    refund = db.query(RefundLedger).get(refund_id)
    if not refund:
        raise ValueError(f"Refund #{refund_id} not found")
    
    if refund.status == "posted":
        return {"status": "already_posted", "refund_id": refund_id}
    
    if refund.status not in ("approved", "pending"):
        raise ValueError(f"Refund #{refund_id} cannot be posted (status: {refund.status})")
    
    order = db.query(Order).get(refund.order_id)
    if not order:
        raise ValueError(f"Order #{refund.order_id} not found for refund #{refund_id}")
    
    cc = country_code or order.country_code
    
    # Get refund amounts
    customer_refund = Decimal(str(refund.customer_refund_amount or 0))
    commission_reversal = Decimal(str(refund.commission_reversal or 0))
    vat_adjustment = Decimal(str(refund.vat_adjustment or 0))
    supplier_deduction = Decimal(str(refund.supplier_reversal or 0))
    
    lines = []
    
    # 1. Refund liability: Dr 2030 Customer Refund Reserve
    if customer_refund > 0:
        if order.payment_method == "card":
            # Card refund goes through gateway
            lines.append(JournalLineInput(
                account_code="2030",
                side="debit",
                amount=customer_refund,
                description=f"Customer refund liability - Order #{order.id}",
            ))
            lines.append(JournalLineInput(
                account_code="1020",
                side="credit",
                amount=customer_refund,
                description=f"Gateway clearing - refund to card - Order #{order.id}",
            ))
        else:
            # COD refund from cash
            lines.append(JournalLineInput(
                account_code="2030",
                side="debit",
                amount=customer_refund,
                description=f"Customer refund liability - Order #{order.id}",
            ))
            lines.append(JournalLineInput(
                account_code="1010",
                side="credit",
                amount=customer_refund,
                description=f"Cash operating - COD refund - Order #{order.id}",
            ))
    
    # 2. Commission reversal: Dr 4010 / Cr 2030
    if commission_reversal > 0:
        lines.append(JournalLineInput(
            account_code="4010",
            side="debit",
            amount=commission_reversal,
            description=f"Commission revenue reversal - Order #{order.id}",
        ))
        lines.append(JournalLineInput(
            account_code="2030",
            side="credit",
            amount=commission_reversal,
            description=f"Refund reserve from commission reversal - Order #{order.id}",
        ))
    
    # 3. VAT reversal: Dr 2040 / Cr 2030
    if vat_adjustment > 0:
        lines.append(JournalLineInput(
            account_code="2040",
            side="debit",
            amount=vat_adjustment,
            description=f"VAT payable reversal - Order #{order.id}",
        ))
        lines.append(JournalLineInput(
            account_code="2030",
            side="credit",
            amount=vat_adjustment,
            description=f"Refund reserve from VAT reversal - Order #{order.id}",
        ))
    
    # 4. Supplier deduction: Dr 2010 / Cr 2030
    if supplier_deduction > 0:
        lines.append(JournalLineInput(
            account_code="2010",
            side="debit",
            amount=supplier_deduction,
            description=f"Supplier payable deduction - Order #{order.id}",
        ))
        lines.append(JournalLineInput(
            account_code="2030",
            side="credit",
            amount=supplier_deduction,
            description=f"Refund reserve from supplier deduction - Order #{order.id}",
        ))
    
    if not lines:
        return {"status": "no_amounts", "refund_id": refund_id}
    
    # Create journal entry
    entry_data = JournalEntryCreate(
        entry_date=_utcnow(),
        reference_type="refund",
        reference_id=refund.id,
        reference_number=f"REF-{refund.id:06d}",
        description=f"Refund posted for Order #{order.id} - {order.order_number}",
        currency=refund.currency or order.currency or "OMR",
        country_code=cc,
        lines=lines,
    )
    
    result = gl.create_journal_entry(db, entry_data)
    
    # Update refund status
    refund.status = "posted"
    refund.processed_at = _utcnow()
    refund.performed_by = approved_by
    db.commit()
    
    # Create supplier deduction record if applicable
    if supplier_deduction > 0 and order.supplier_id:
        _create_supplier_deduction(db, order, supplier_deduction, refund.id, cc)
    
    _log_refund(db, "refund_posted", refund_id, {
        "order_id": order.id,
        "customer_refund": float(customer_refund),
        "commission_reversal": float(commission_reversal),
        "vat_adjustment": float(vat_adjustment),
        "supplier_deduction": float(supplier_deduction),
        "journal_entry_id": result.id,
    }, cc)
    
    return {
        "status": "posted",
        "refund_id": refund_id,
        "journal_entry_id": result.id,
        "customer_refund": float(customer_refund),
        "commission_reversal": float(commission_reversal),
        "vat_adjustment": float(vat_adjustment),
        "supplier_deduction": float(supplier_deduction),
    }


def _create_supplier_deduction(
    db: Session,
    order: Order,
    amount: Decimal,
    refund_id: int,
    country_code: str = None,
):
    """Create a negative supplier settlement for the refund deduction."""
    settlement = SupplierSettlement(
        supplier_id=order.supplier_id,
        order_id=order.id,
        gross_amount=Decimal("0"),
        commission_amount=Decimal("0"),
        net_amount=-amount,  # Negative = deduction
        status="deducted",
        currency=order.currency or "OMR",
        country_code=country_code,
    )
    db.add(settlement)
    db.flush()
    
    # Link refund to settlement
    refund = db.query(RefundLedger).get(refund_id)
    if refund:
        refund.ledger_id = settlement.id


def _log_refund(db: Session, kind: str, entity_id: int, detail: dict, country_code: str = None):
    """Log refund posting activity."""
    try:
        db.add(FinanceAutomationLog(
            kind=kind,
            records_processed=1,
            records_changed=1,
            detail={**detail, "entity_id": entity_id},
            country_code=country_code,
        ))
        db.add(FinanceAuditLog(
            action="journal_post",
            entity_type="refund",
            entity_id=entity_id,
            detail=detail,
            country_code=country_code,
        ))
        db.commit()
    except Exception as e:
        logger.warning("Refund log failed: %s", e)
        db.rollback()
