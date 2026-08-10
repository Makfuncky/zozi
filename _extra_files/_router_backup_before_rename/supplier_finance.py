"""
Supplier Finance Router
=======================
Exposes payment-status and payout-status for each order so the supplier panel
can show which orders are paid, which payouts are completed/pending, and the
current settlement balance.

Integrates with:
  - ``SupplierSettlement`` — per-order settlement record
  - ``LogisticsSettlement`` — per-order logistics settlement
  - ``Payout`` — actual payout to supplier bank account
  - ``TransactionLedger`` — detailed financial breakdown
  - ``SupplierBankAccount`` — linked bank account for payouts

Flow (from the user's spec):
  1. Order is delivered → status = "completed"
  2. After 10-day hold → SupplierSettlement becomes eligible
  3. Payout is created → transferred to SupplierBankAccount
  4. Supplier sees status in payout page and order page
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from db.database import get_db
from models import (
    Order, OrderItem, SupplierProfile, SupplierSettlement,
    SupplierBankAccount, Payout, TransactionLedger, User,
)
from utils.dependencies import require_supplier
from utils.datetime_utils import utcnow

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_user_id(current_user: User | dict) -> int:
    """Normalise current_user to an int ID (supports both dict and ORM)."""
    if isinstance(current_user, dict):
        uid = current_user.get("id") or current_user.get("user_id")
        if not uid:
            raise HTTPException(status_code=401, detail="Invalid user session")
        return int(uid)
    return current_user.id


# ── Helper: derive payout eligibility date (order completed + 10 days) ───


def _payout_eligible_at(completed_at: Optional[datetime]) -> Optional[datetime]:
    """Return the date when payout becomes eligible (10 days after completion)."""
    if not completed_at:
        return None
    return completed_at + timedelta(days=10)


# ═══════════════════════════════════════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════════════════════════════════════


@router.get("/payout-status/summary")
def get_supplier_payout_summary(
    current_user: User = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    """Return aggregate payout stats for the supplier dashboard."""
    user_id = _get_user_id(current_user)

    # Total pending payout amount (completed orders not yet paid out)
    pending_settlements = (
        db.query(SupplierSettlement)
        .filter(
            SupplierSettlement.supplier_id == user_id,
            SupplierSettlement.status.in_(["pending", "eligible"]),
        )
        .all()
    )
    total_pending = sum(float(s.net_amount or 0) for s in pending_settlements)

    # Total paid out
    paid_payouts = (
        db.query(Payout)
        .filter(
            Payout.user_id == user_id,
            Payout.status == "completed",
        )
        .all()
    )
    total_paid = sum(float(p.amount or 0) for p in paid_payouts)

    # Bank account status
    bank_account = (
        db.query(SupplierBankAccount)
        .filter(
            SupplierBankAccount.supplier_id == user_id,
            SupplierBankAccount.is_active == True,
        )
        .first()
    )

    return {
        "total_pending_payout": round(total_pending, 3),
        "total_paid_out": round(total_paid, 3),
        "pending_count": len(pending_settlements),
        "paid_count": len(paid_payouts),
        "bank_account_configured": bank_account is not None,
        "bank_account_verified": bool(bank_account and bank_account.verification_status == "verified"),
        "bank_account": {
            "bank_name": bank_account.bank_name if bank_account else None,
            "beneficiary_name": bank_account.beneficiary_name if bank_account else None,
            "iban_last4": bank_account.iban[-4:] if bank_account and bank_account.iban else None,
            "currency": bank_account.currency if bank_account else None,
        } if bank_account else None,
    }


@router.get("/orders/{order_id}/payment-status")
def get_order_payment_status(
    order_id: int,
    current_user: User = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    """Return detailed payment + payout status for a single order.

    Shows:
      - Order payment status (paid / unpaid / refunded)
      - Payment method (COD / card)
      - Settlement amount and status
      - Payout eligibility date (completed_at + 10 days)
      - Payout status (pending / completed)
      - Financial breakdown (product cost, VAT, gateway fee, commission, net)
    """
    user_id = _get_user_id(current_user)

    # Verify supplier owns this order
    order = (
        db.query(Order)
        .filter(Order.id == order_id)
        .join(OrderItem)
        .filter(OrderItem.supplier_id == user_id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found for this supplier")

    # Settlement record
    settlement = (
        db.query(SupplierSettlement)
        .filter(
            SupplierSettlement.supplier_id == user_id,
            SupplierSettlement.order_id == order_id,
        )
        .first()
    )

    # Payout record linked via settlement
    payout = None
    if settlement and settlement.payout_id:
        payout = db.query(Payout).filter(Payout.id == settlement.payout_id).first()

    # Financial breakdown from TransactionLedger
    ledger = (
        db.query(TransactionLedger)
        .filter(
            TransactionLedger.order_id == order_id,
            TransactionLedger.supplier_id == user_id,
        )
        .first()
    )

    # Derive payout eligibility
    completed_at = getattr(order, "completed_at", None) or getattr(order, "delivered_at", None)
    eligible_at = _payout_eligible_at(completed_at)
    now = datetime.now(timezone.utc)
    days_until_eligible = None
    if eligible_at and eligible_at > now:
        days_until_eligible = (eligible_at - now).days

    return {
        "order_id": order.id,
        "order_number": getattr(order, "order_number", f"ORD-{order.id}"),
        "order_status": order.status,
        "payment_method": getattr(order, "payment_method", "unknown"),
        "payment_status": getattr(order, "payment_status", "unpaid"),
        "total_amount": float(order.total or 0),
        "completed_at": completed_at.isoformat() if completed_at else None,
        "settlement": {
            "id": settlement.id if settlement else None,
            "gross_amount": float(settlement.gross_amount) if settlement else None,
            "commission_amount": float(settlement.commission_amount) if settlement else None,
            "vat_amount": float(getattr(settlement, "vat_on_commission", 0) or 0),
            "net_amount": float(settlement.net_amount) if settlement else None,
            "status": settlement.status if settlement else "not_settled",
            "eligible_at": settlement.eligible_at.isoformat() if settlement and settlement.eligible_at else eligible_at.isoformat() if eligible_at else None,
            "created_at": settlement.created_at.isoformat() if settlement else None,
        } if settlement else None,
        "payout": {
            "id": payout.id if payout else None,
            "amount": float(payout.amount) if payout else None,
            "status": payout.status if payout else "not_initiated",
            "created_at": payout.created_at.isoformat() if payout else None,
            "completed_at": payout.completed_at.isoformat() if payout and hasattr(payout, "completed_at") and payout.completed_at else None,
        } if payout else None,
        "payout_eligibility": {
            "eligible_at": eligible_at.isoformat() if eligible_at else None,
            "days_remaining": days_until_eligible if days_until_eligible is not None else 0,
            "is_eligible": eligible_at is not None and now >= eligible_at if eligible_at else False,
            "hold_days": 10,
        },
        "financial_breakdown": {
            "product_subtotal": float(ledger.product_subtotal) if ledger and ledger.product_subtotal else 0,
            "discount_amount": float(ledger.discount_amount) if ledger and ledger.discount_amount else 0,
            "delivery_pickup_charge": float(ledger.delivery_pickup_charge) if ledger and ledger.delivery_pickup_charge else 0,
            "delivery_dropoff_charge": float(ledger.delivery_dropoff_charge) if ledger and ledger.delivery_dropoff_charge else 0,
            "vat_amount": float(ledger.vat_amount) if ledger and ledger.vat_amount else 0,
            "zozi_commission": float(ledger.zozi_commission) if ledger and ledger.zozi_commission else 0,
            "net_supplier_amount": float(ledger.net_supplier_amount) if ledger and ledger.net_supplier_amount else 0,
        } if ledger else None,
    }


@router.get("/payout-status/orders")
def list_supplier_orders_with_payout_status(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, description="Filter by settlement status: pending, eligible, paid"),
    current_user: User = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    """Return all orders for this supplier with their payment + payout status.

    Used by the supplier panel payout page and order page to show:
      - Which orders are paid / unpaid
      - Which payouts are completed / pending
      - Settlement details for each order
    """
    user_id = _get_user_id(current_user)

    # Base query: orders with items for this supplier
    base = (
        db.query(Order)
        .join(OrderItem)
        .filter(OrderItem.supplier_id == user_id)
        .distinct()
    )

    total = base.count()
    orders = (
        base
        .order_by(desc(Order.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    # Collect settlement + payout data for these orders
    order_ids = [o.id for o in orders]
    settlements = {
        s.order_id: s
        for s in db.query(SupplierSettlement)
        .filter(
            SupplierSettlement.supplier_id == user_id,
            SupplierSettlement.order_id.in_(order_ids),
        )
        .all()
    }
    payout_ids = [s.payout_id for s in settlements.values() if s.payout_id]
    payouts = {
        p.id: p
        for p in db.query(Payout)
        .filter(Payout.id.in_(payout_ids))
        .all()
    } if payout_ids else {}

    now = datetime.now(timezone.utc)

    items = []
    for order in orders:
        settlement = settlements.get(order.id)
        payout = payouts.get(settlement.payout_id) if settlement and settlement.payout_id else None

        completed_at = getattr(order, "completed_at", None) or getattr(order, "delivered_at", None)
        eligible_at = _payout_eligible_at(completed_at)

        items.append({
            "order_id": order.id,
            "order_number": getattr(order, "order_number", f"ORD-{order.id}"),
            "order_status": order.status,
            "payment_method": getattr(order, "payment_method", "unknown"),
            "payment_status": getattr(order, "payment_status", "unpaid"),
            "total_amount": float(order.total or 0),
            "created_at": order.created_at.isoformat() if order.created_at else None,
            "completed_at": completed_at.isoformat() if completed_at else None,
            "settlement_status": settlement.status if settlement else "not_settled",
            "settlement_net_amount": float(settlement.net_amount) if settlement else None,
            "payout_status": payout.status if payout else ("pending_settlement" if settlement else "not_settled"),
            "payout_amount": float(payout.amount) if payout else None,
            "payout_eligible_at": eligible_at.isoformat() if eligible_at else None,
            "payout_days_remaining": max(0, (eligible_at - now).days) if eligible_at and eligible_at > now else 0,
        })

    # Apply client-side filter if status_filter set
    if status_filter:
        items = [i for i in items if i.get("settlement_status") == status_filter or i.get("payout_status") == status_filter]

    return {
        "data": items,
        "total": len(orders),
        "page": page,
        "page_size": page_size,
        "filters_applied": bool(status_filter),
    }


@router.get("/bank-account")
def get_supplier_bank_account(
    current_user: User = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    """Return the supplier's bank account details."""
    user_id = _get_user_id(current_user)
    account = (
        db.query(SupplierBankAccount)
        .filter(
            SupplierBankAccount.supplier_id == user_id,
            SupplierBankAccount.is_active == True,
        )
        .first()
    )
    if not account:
        return {"configured": False, "account": None}
    return {
        "configured": True,
        "account": {
            "id": account.id,
            "bank_name": account.bank_name,
            "beneficiary_name": account.beneficiary_name,
            "account_number": f"****{account.account_number[-4:]}" if account.account_number else None,
            "iban": f"****{account.iban[-4:]}" if account.iban else None,
            "swift_code": account.swift_code,
            "currency": account.currency,
            "bank_country": account.bank_country,
            "verification_status": account.verification_status,
            "is_active": account.is_active,
        },
    }


@router.put("/bank-account")
def upsert_supplier_bank_account(
    payload: dict,
    current_user: User = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    """Create or update the supplier's bank account."""
    user_id = _get_user_id(current_user)

    account = (
        db.query(SupplierBankAccount)
        .filter(SupplierBankAccount.supplier_id == user_id)
        .first()
    )

    if not account:
        account = SupplierBankAccount(supplier_id=user_id)
        db.add(account)

    # Update fields from payload
    for field in ["bank_name", "beneficiary_name", "account_number", "iban",
                  "swift_code", "routing_number", "branch_name", "currency", "bank_country"]:
        if field in payload:
            setattr(account, field, str(payload[field]).strip())

    account.is_active = True
    db.commit()
    db.refresh(account)

    return {
        "status": "success",
        "message": "Bank account updated",
        "verification_status": account.verification_status,
    }
