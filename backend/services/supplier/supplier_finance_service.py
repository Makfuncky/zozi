"""
Supplier Finance Service
=======================
Read/write helpers for supplier payment-status and payout-status endpoints.

This module owns the DB work that previously lived in ``routers/supplier/
supplier_finance.py`` so the router stays a thin delegator (layering: LC1/W1).

Integrates with:
  - ``SupplierSettlement`` — per-order settlement record
  - ``LogisticsSettlement`` — per-order logistics settlement
  - ``Payout`` — actual payout to supplier bank account
  - ``TransactionLedger`` — detailed financial breakdown
  - ``SupplierBankAccount`` — linked bank account for payouts
"""
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from data.models import (
    Order,
    OrderItem,
    SupplierBankAccount,
    SupplierSettlement,
    Payout,
    TransactionLedger,
)
from utils.pagination import cursor_paginate_desc
from data.services_write_helpers import add_and_flush, commit_and_refresh


def _get_user_id(current_user) -> int:
    """Normalise current_user to an int ID (supports both dict and ORM)."""
    if isinstance(current_user, dict):
        uid = current_user.get("id") or current_user.get("user_id")
        if not uid:
            raise HTTPException(status_code=401, detail="Invalid user session")
        return int(uid)
    return current_user.id


def _payout_eligible_at(completed_at) -> Optional["datetime"]:  # noqa: F821
    """Return the date when payout becomes eligible (10 days after completion)."""
    from datetime import timedelta

    if not completed_at:
        return None
    return completed_at + timedelta(days=10)


def get_payout_summary(db: Session, current_user, skip: int = 0, limit: int = 20) -> dict:
    """Return aggregate payout stats for the supplier dashboard."""
    user_id = _get_user_id(current_user)

    pending_settlements = (
        db.query(SupplierSettlement)
        .filter(
            SupplierSettlement.supplier_id == user_id,
            SupplierSettlement.status.in_(["pending", "eligible"]),
        )
        .offset(skip).limit(limit)
        .all()
    )
    total_pending = sum(float(s.net_amount or 0) for s in pending_settlements)

    paid_payouts = (
        db.query(Payout)
        .filter(
            Payout.user_id == user_id,
            Payout.status == "completed",
        )
        .offset(skip).limit(limit)
        .all()
    )
    total_paid = sum(float(p.amount or 0) for p in paid_payouts)

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


def get_order_payment_status(db: Session, current_user, order_id: int) -> dict:
    """Return detailed payment + payout status for a single order."""
    from datetime import datetime, timezone

    user_id = _get_user_id(current_user)

    order = (
        db.query(Order)
        .filter(Order.id == order_id)
        .join(OrderItem)
        .filter(OrderItem.supplier_id == user_id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found for this supplier")

    settlement = (
        db.query(SupplierSettlement)
        .filter(
            SupplierSettlement.supplier_id == user_id,
            SupplierSettlement.order_id == order_id,
        )
        .first()
    )

    payout = None
    if settlement and settlement.payout_id:
        payout = db.query(Payout).filter(Payout.id == settlement.payout_id).first()

    ledger = (
        db.query(TransactionLedger)
        .filter(
            TransactionLedger.order_id == order_id,
            TransactionLedger.supplier_id == user_id,
        )
        .first()
    )

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


def list_orders_with_payout_status(
    db: Session,
    current_user,
    cursor: Optional[str] = None,
    limit: int = 20,
    status_filter: Optional[str] = None,
):
    """Return all orders for this supplier with their payment + payout status."""
    from datetime import datetime, timezone

    user_id = _get_user_id(current_user)

    base = (
        db.query(Order)
        .join(OrderItem)
        .filter(OrderItem.supplier_id == user_id)
        .distinct()
    )

    page = cursor_paginate_desc(base.order_by(Order.id.desc()), cursor=cursor, page_size=limit)

    orders = page.items

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

    if status_filter:
        items = [i for i in items if i.get("settlement_status") == status_filter or i.get("payout_status") == status_filter]

    page.items = items
    return page


def get_bank_account(db: Session, current_user) -> dict:
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


def upsert_bank_account(db: Session, current_user, payload: dict) -> dict:
    """Create or update the supplier's bank account."""
    user_id = _get_user_id(current_user)

    account = (
        db.query(SupplierBankAccount)
        .filter(SupplierBankAccount.supplier_id == user_id)
        .first()
    )

    if not account:
        account = SupplierBankAccount(supplier_id=user_id)
        add_and_flush(db, account)

    for field in ["bank_name", "beneficiary_name", "account_number", "iban",
                  "swift_code", "routing_number", "branch_name", "currency", "bank_country"]:
        if field in payload:
            setattr(account, field, str(payload[field]).strip())

    account.is_active = True
    commit_and_refresh(db, account)

    return {
        "status": "success",
        "message": "Bank account updated",
        "verification_status": account.verification_status,
    }
