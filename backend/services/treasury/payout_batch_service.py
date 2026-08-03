"""
Payout Batch Service — Smart automated payout generation.

Handles:
  - #14: Smart Payout Batch Generation (nightly cron gathers eligible settlements)
  - #15: Supplier Self-Approval (SMS/email link for supplier approval)
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from data.models import (
    PayoutBatch,
    PayoutBatchItem,
    SupplierSettlement,
    LogisticsPartnerPayout,
    Vendor,
    LogisticsPartner,
    FinanceAutomationLog,
    FinanceAuditLog,
)
from data.schemas import JournalEntryCreate, JournalLineInput
from services import general_ledger_service as gl
from utils.datetime_utils import utcnow as _utcnow

logger = logging.getLogger(__name__)

# Payout configuration
PAYOUT_HOLDING_DAYS = 7       # Days to hold before payout eligible
MIN_PAYOUT_AMOUNT = Decimal("10.00")  # Minimum payout threshold
BATCH_LIMIT = 200             # Max items per batch


# ── #14: Smart Payout Batch Generation ─────────────────────────────────────


def generate_supplier_payout_batches(
    db: Session,
    country_code: str = None,
    holding_days: int = PAYOUT_HOLDING_DAYS,
) -> dict:
    """
    Nightly cron: Gather eligible supplier settlements and create payout batches.
    
    Logic:
    1. Find all settlements with status='pending' and age > holding_days
    2. Group by supplier
    3. Create batch items for each supplier meeting minimum threshold
    4. Generate batch header with total
    5. Return batches ready for supplier approval
    """
    cutoff_date = _utcnow() - timedelta(days=holding_days)
    
    # Find eligible settlements
    q = db.query(SupplierSettlement).filter(
        SupplierSettlement.status == "pending",
        SupplierSettlement.created_at <= cutoff_date,
    )
    if country_code:
        q = q.filter(SupplierSettlement.country_code == country_code)
    
    settlements = q.all()
    
    if not settlements:
        return {"batches_created": 0, "message": "No eligible settlements"}
    
    # Group by supplier
    supplier_settlements: dict[int, list] = {}
    for s in settlements:
        sid = s.supplier_id
        if sid not in supplier_settlements:
            supplier_settlements[sid] = []
        supplier_settlements[sid].append(s)
    
    batches_created = 0
    total_items = 0
    
    for supplier_id, supplier_s_settlements in supplier_settlements.items():
        total_amount = sum(Decimal(str(s.net_amount or 0)) for s in supplier_s_settlements)
        
        # Skip if below minimum
        if total_amount < MIN_PAYOUT_AMOUNT:
            continue
        
        # Create batch
        batch = _create_payout_batch(
            db,
            entity_type="supplier",
            entity_id=supplier_id,
            settlements=supplier_s_settlements,
            total_amount=total_amount,
            country_code=country_code,
        )
        batches_created += 1
        
        # Send approval email to supplier
        try:
            from services.transactional_email_service import enqueue_supplier_approval_email
            enqueue_supplier_approval_email(
                supplier_id, batch.id, batch.batch_number, float(total_amount)
            )
        except Exception as e:
            logger.warning("Failed to send approval email for batch %s: %s", batch.id, e)
        total_items += len(supplier_s_settlements)
    
    db.commit()
    
    _log_automation(db, "payout_batch_generation", len(settlements), total_items, {
        "batches_created": batches_created,
        "suppliers_processed": len(supplier_settlements),
    }, country_code)
    
    return {
        "batches_created": batches_created,
        "total_settlements": len(settlements),
        "total_items": total_items,
    }


def generate_logistics_payout_batches(
    db: Session,
    country_code: str = None,
    holding_days: int = 7,
) -> dict:
    """Generate payout batches for logistics partners (COD remittances)."""
    cutoff_date = _utcnow() - timedelta(days=holding_days)
    
    q = db.query(LogisticsPartnerPayout).filter(
        LogisticsPartnerPayout.status == "pending",
        LogisticsPartnerPayout.created_at <= cutoff_date,
    )
    if country_code:
        q = q.filter(LogisticsPartnerPayout.country_code == country_code)
    
    payouts = q.all()
    
    if not payouts:
        return {"batches_created": 0, "message": "No eligible logistics payouts"}
    
    # Group by logistics partner
    partner_payouts: dict[int, list] = {}
    for p in payouts:
        pid = p.logistics_partner_id
        if pid not in partner_payouts:
            partner_payouts[pid] = []
        partner_payouts[pid].append(p)
    
    batches_created = 0
    
    for partner_id, partner_payouts_list in partner_payouts.items():
        total_amount = sum(Decimal(str(p.net_amount or 0)) for p in partner_payouts_list)
        
        if total_amount < MIN_PAYOUT_AMOUNT:
            continue
        
        batch = _create_payout_batch(
            db,
            entity_type="logistics",
            entity_id=partner_id,
            settlements=partner_payouts_list,
            total_amount=total_amount,
            country_code=country_code,
        )
        batches_created += 1
    
    db.commit()
    
    _log_automation(db, "logistics_payout_batch", len(payouts), batches_created, {
        "batches_created": batches_created,
    }, country_code)
    
    return {"batches_created": batches_created, "total_payouts": len(payouts)}


def _create_payout_batch(
    db: Session,
    entity_type: str,
    entity_id: int,
    settlements: list,
    total_amount: Decimal,
    country_code: str = None,
) -> PayoutBatch:
    """Create a payout batch with items."""
    batch_number = f"PB-{entity_type[:3].upper()}-{uuid.uuid4().hex[:8].upper()}"
    
    batch = PayoutBatch(
        batch_number=batch_number,
        country_code=country_code,
        total_amount=total_amount,
        item_count=len(settlements),
        status="generated",
        created_by=1,  # System user
    )
    db.add(batch)
    db.flush()
    
    for settlement in settlements:
        item = PayoutBatchItem(
            batch_id=batch.id,
            entity_type=entity_type,
            entity_id=entity_id,
            amount=settlement.net_amount or Decimal("0"),
            currency=settlement.currency or "OMR",
            reference=f"Settlement #{settlement.id}",
            status="pending",
            country_code=country_code,
        )
        db.add(item)
        
        # Mark settlement as batched
        settlement.status = "batched"
        settlement.payout_id = batch.id
    
    return batch


# ── #15: Supplier Self-Approval ────────────────────────────────────────────


def get_pending_batches_for_supplier(
    db: Session,
    supplier_id: int,
) -> list[dict]:
    """Get payout batches pending supplier approval."""
    batches = db.query(PayoutBatch).filter(
        PayoutBatch.status == "generated",
        PayoutBatch.items.any(
            PayoutBatchItem.entity_type == "supplier",
            PayoutBatchItem.entity_id == supplier_id,
        ),
    ).all()
    
    return [
        {
            "batch_id": b.id,
            "batch_number": b.batch_number,
            "total_amount": float(b.total_amount or 0),
            "item_count": b.item_count,
            "created_at": b.created_at.isoformat() if b.created_at else None,
        }
        for b in batches
    ]


def supplier_approve_batch(
    db: Session,
    batch_id: int,
    supplier_id: int,
    approved: bool = True,
    notes: str = None,
) -> dict:
    """
    Supplier approves or rejects a payout batch via self-service link.
    
    On approval: status -> 'supplier_approved'
    On rejection: status -> 'supplier_rejected'
    """
    batch = db.query(PayoutBatch).get(batch_id)
    if not batch:
        raise ValueError(f"Batch #{batch_id} not found")
    
    # Verify supplier has items in this batch
    has_items = db.query(PayoutBatchItem).filter(
        PayoutBatchItem.batch_id == batch_id,
        PayoutBatchItem.entity_type == "supplier",
        PayoutBatchItem.entity_id == supplier_id,
    ).first()
    
    if not has_items:
        raise ValueError(f"Supplier #{supplier_id} has no items in batch #{batch_id}")
    
    if batch.status != "generated":
        raise ValueError(f"Batch #{batch_id} is not in 'generated' status (current: {batch.status})")
    
    if approved:
        batch.status = "supplier_approved"
        batch.notes = notes or f"Approved by supplier #{supplier_id}"
    else:
        batch.status = "supplier_rejected"
        batch.notes = notes or f"Rejected by supplier #{supplier_id}"
    
    db.commit()
    
    _log_automation(db, "supplier_approval", batch_id, {
        "approved": approved,
        "supplier_id": supplier_id,
    }, batch.country_code)
    
    return {
        "batch_id": batch_id,
        "status": batch.status,
        "approved": approved,
    }


# ── Helper ─────────────────────────────────────────────────────────────────


def _log_automation(db: Session, kind: str, processed: int, changed: int,
                     detail: dict = None, country_code: str = None):
    try:
        db.add(FinanceAutomationLog(
            kind=kind,
            records_processed=processed,
            records_changed=changed,
            detail=detail,
            country_code=country_code,
        ))
        db.commit()
    except Exception as e:
        logger.warning("Automation log failed: %s", e)
        db.rollback()
