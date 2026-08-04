"""
Supplier Finance Router
======================
Exposes payment-status and payout-status for each order so the supplier panel
can show which orders are paid, which payouts are completed/pending, and the
current settlement balance.

All DB work is delegated to ``services/supplier/supplier_finance_service.py``
so this router stays a thin delegator (layering: LC1/W1).

Flow (from the user's spec):
  1. Order is delivered â†’ status = "completed"
  2. After 10-day hold â†’ SupplierSettlement becomes eligible
  3. Payout is created â†’ transferred to SupplierBankAccount
  4. Supplier sees status in payout page and order page
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from data.db import get_db
from data.schemas import CursorPage
from data.models import User
from utils.dependencies import require_supplier
from services.supplier.supplier_finance_service import (
    get_payout_summary,
    get_order_payment_status,
    list_orders_with_payout_status,
    get_bank_account,
    upsert_bank_account,
)

from services.write_helpers import add_and_flush, commit_and_refresh
logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/payout-status/summary")
def get_supplier_payout_summary(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    """Return aggregate payout stats for the supplier dashboard."""
    return get_payout_summary(db, current_user, skip=skip, limit=limit)


@router.get("/orders/{order_id}/payment-status")
def get_order_payment_status_route(
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
    return get_order_payment_status(db, current_user, order_id)


@router.get("/payout-status/orders", response_model=CursorPage)
def list_supplier_orders_with_payout_status(
    cursor: str | None = Query(None, description="Cursor for next page"),
    limit: int = Query(20, ge=1, le=100),
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
    return list_orders_with_payout_status(
        db, current_user, cursor=cursor, limit=limit, status_filter=status_filter
    )


@router.get("/bank-account")
def get_supplier_bank_account(
    current_user: User = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    """Return the supplier's bank account details."""
    return get_bank_account(db, current_user)


@router.put("/bank-account")
def upsert_supplier_bank_account(
    payload: dict,
    current_user: User = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    """Create or update the supplier's bank account."""
    return upsert_bank_account(db, current_user, payload)
