"""
Supplier Finance Router
=======================
Exposes payment-status and payout-status for each order so the supplier panel
can show which orders are paid, which payouts are completed/pending, and the
current settlement balance. See ``services.supplier.supplier_finance_service``
for the owned DB logic.
"""
from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from infrastructure.database.database import get_db
from domains.accounts.models.user import User
from infrastructure.utils.dependencies import require_supplier
from domains.suppliers.services.supplier_finance_service import get_order_payment_status
from domains.suppliers.services.supplier_finance_service import get_supplier_bank_account
from domains.suppliers.services.supplier_finance_service import get_supplier_payout_summary
from domains.suppliers.services.supplier_finance_service import list_supplier_orders_with_payout_status
from domains.suppliers.services.supplier_finance_service import upsert_supplier_bank_account

router = APIRouter(prefix="/api/v1/supplier")


def _get_user_id(current_user: User | dict) -> int:
    """Normalise current_user to an int ID (supports both dict and ORM)."""
    if isinstance(current_user, dict):
        uid = current_user.get("id") or current_user.get("user_id")
        if not uid:
            raise HTTPException(status_code=401, detail="Invalid user session")
        return int(uid)
    return current_user.id


@router.get("/payout-status/summary")
def get_supplier_payout_summary(
    current_user: User = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    """Return aggregate payout stats for the supplier dashboard."""
    return get_supplier_payout_summary(db, _get_user_id(current_user))


@router.get("/orders/{order_id}/payment-status")
def get_order_payment_status_route(
    order_id: int,
    current_user: User = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    """Return detailed payment + payout status for a single order."""
    return get_order_payment_status(db, order_id, _get_user_id(current_user))


@router.get("/payout-status/orders")
def list_supplier_orders_with_payout_status_route(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, description="Filter by settlement status: pending, eligible, paid"),
    current_user: User = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    """Return all orders for this supplier with their payment + payout status."""
    return list_supplier_orders_with_payout_status(
        db, _get_user_id(current_user), page, page_size, status_filter
    )


@router.get("/bank-account")
def get_supplier_bank_account_route(
    current_user: User = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    """Return the supplier's bank account details."""
    return get_supplier_bank_account(db, _get_user_id(current_user))


@router.put("/bank-account")
def upsert_supplier_bank_account_route(
    payload: dict,
    current_user: User = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    """Create or update the supplier's bank account."""
    return upsert_supplier_bank_account(db, _get_user_id(current_user), payload)
