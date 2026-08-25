"""Supplier finance router — consolidated from 5 source files."""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status


router = APIRouter(prefix="/api/v1/supplier/finance", tags=["supplier", "finance"])


# === From commission.py ===
"""
Commission Router — admin endpoints for managing the full commission engine.
All endpoints require admin role.
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from domains.finance.services._auto_stubs import commission_controller
from infrastructure.utils.dependencies import require_admin
from infrastructure.database.database import get_db
from infrastructure.database.schemas import ListPage


# ── Pydantic schemas ─────────────────────────────────────────────────────────

class CommissionRateBody(BaseModel):
    rate: float = Field(..., ge=0.0, le=1.0, description="Commission rate as decimal, e.g. 0.12 for 12%")
    note: Optional[str] = Field(None, max_length=500)


class GlobalConfigBody(BaseModel):
    default_rate: Optional[float] = Field(None, ge=0.0, le=1.0)
    low_value_threshold: Optional[float] = Field(None, ge=0.0)
    fixed_cap_amount: Optional[float] = Field(None, ge=0.0)
    fixed_cap_enabled: Optional[bool] = None
    margin_protection_enabled: Optional[bool] = None
    margin_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)


class CategoryRateBody(BaseModel):
    rate: Optional[float] = Field(None, ge=0.0, le=1.0)
    is_active: Optional[bool] = None
    notes: Optional[str] = Field(None, max_length=500)
    category_display_name: Optional[str] = Field(None, max_length=150)


class BadgeTierBody(BaseModel):
    commission_rate: Optional[float] = Field(None, ge=0.0, le=1.0)
    setup_fee: Optional[float] = Field(None, ge=0.0)
    recurring_fee: Optional[float] = Field(None, ge=0.0)
    recurring_interval: Optional[str] = Field(None, max_length=20)
    benefits_json: Optional[str] = None
    min_fulfilled_orders: Optional[int] = None
    min_monthly_revenue: Optional[float] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class LedgerAdjustmentBody(BaseModel):
    new_amount: float = Field(..., ge=0.0)
    reason: str = Field(..., min_length=5, max_length=1000)


class PreviewBody(BaseModel):
    supplier_id: int
    order_value: float = Field(..., gt=0.0)
    category_slug: Optional[str] = None


# ── Global config ─────────────────────────────────────────────────────────────

@router.get("/global", summary="Get global commission config")
def get_global_config(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    return commission_controller.get_global_config(db)


@router.put("/global", summary="Update global commission config")
def update_global_config(
    body: GlobalConfigBody,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    payload = {k: v for k, v in body.model_dump().items() if v is not None}
    return commission_controller.update_global_config(payload, current_user, db)


# ── Category rates ────────────────────────────────────────────────────────────

@router.get("/categories", response_model=ListPage[dict], summary="List all category commission rates")
def list_category_rates(
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    return commission_controller.list_category_rates(db, limit=page_size, offset=(page - 1) * page_size, search=search)


@router.put("/categories/{category_slug}", summary="Update a category commission rate")
def update_category_rate(
    category_slug: str,
    body: CategoryRateBody,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    payload = {k: v for k, v in body.model_dump().items() if v is not None}
    return commission_controller.update_category_rate(category_slug, payload, current_user, db)


# ── Badge tiers ───────────────────────────────────────────────────────────────

@router.get("/badge-tiers", response_model=ListPage[dict], summary="List all badge tiers")
def list_badge_tiers(
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    return commission_controller.list_badge_tiers(db, limit=page_size, offset=(page - 1) * page_size, search=search)


@router.put("/badge-tiers/{badge_level}", summary="Update a badge tier")
def update_badge_tier(
    badge_level: str,
    body: BadgeTierBody,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    payload = {k: v for k, v in body.model_dump().items() if v is not None}
    return commission_controller.update_badge_tier(badge_level, payload, current_user, db)


# ── Commission ledger ─────────────────────────────────────────────────────────

@router.get("/ledger", summary="List commission ledger entries")
def list_ledger_entries(
    supplier_id: Optional[int] = None,
    order_id: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    return commission_controller.list_ledger_entries(db, supplier_id, order_id, skip, limit)


@router.put("/ledger/{ledger_id}/adjust", summary="Adjust a ledger entry (dispute resolution)")
def adjust_ledger_entry(
    ledger_id: int,
    body: LedgerAdjustmentBody,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    return commission_controller.create_ledger_adjustment(
        ledger_id=ledger_id,
        new_amount=body.new_amount,
        reason=body.reason,
        acting_user=current_user,
        db=db,
    )


# ── Preview calculator (no DB writes) ─────────────────────────────────────────

@router.post("/preview", summary="Preview commission calculation without persisting")
def preview_commission(
    body: PreviewBody,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    return commission_controller.preview_commission(
        supplier_id=body.supplier_id,
        order_value=body.order_value,
        category_slug=body.category_slug,
        db=db,
    )


# ── All suppliers overview ────────────────────────────────────────────────────

@router.get("/suppliers", response_model=ListPage[dict], summary="List all suppliers with current commission rates")
def list_supplier_commissions(
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    return commission_controller.list_all_supplier_commissions(db, limit=page_size, offset=(page - 1) * page_size, search=search)


# ── Supplier-level commission ─────────────────────────────────────────────────

@router.get("/suppliers/{supplier_id}", summary="Get supplier commission rate + history")
def get_supplier_commission(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    return commission_controller.get_supplier_commission(supplier_id, db)


@router.post("/suppliers/{supplier_id}", status_code=201, summary="Set supplier commission override")
def set_supplier_commission(
    supplier_id: int,
    body: CommissionRateBody,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    return commission_controller.set_supplier_commission(
        supplier_id=supplier_id,
        rate=body.rate,
        note=body.note,
        acting_user=current_user,
        db=db,
    )


@router.delete("/suppliers/{supplier_id}", summary="Remove supplier commission override")
def delete_supplier_commission_override(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    return commission_controller.delete_supplier_commission_override(
        supplier_id=supplier_id,
        acting_user=current_user,
        db=db,
    )


# ── Product-level commission override ────────────────────────────────────────

@router.get("/products/{product_id}", summary="Get product commission override")
def get_product_commission_override(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    result = commission_controller.get_product_commission_override(product_id, db)
    if result is None:
        return {"override": None, "message": "No override — using category/badge/default rate"}
    return result


@router.get("/product-overrides", summary="List product commission overrides")
def list_product_commission_overrides(
    search: Optional[str] = None,
    supplier_id: Optional[int] = None,
    limit: int = Query(100, ge=1, le=300),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    return commission_controller.list_product_commission_overrides(
        db,
        search=search,
        supplier_id=supplier_id,
        limit=limit,
    )


@router.post("/products/{product_id}", status_code=201, summary="Set product commission override")
def set_product_commission_override(
    product_id: int,
    body: CommissionRateBody,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    return commission_controller.set_product_commission_override(
        product_id=product_id,
        rate=body.rate,
        note=body.note,
        acting_user=current_user,
        db=db,
    )


@router.delete("/products/{product_id}", summary="Remove product commission override")
def delete_product_commission_override(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    return commission_controller.delete_product_commission_override(
        product_id=product_id,
        acting_user=current_user,
        db=db,
    )


# ── Effective rate calculator (backwards-compatible) ─────────────────────────

@router.get("/effective-rate", summary="Get effective commission rate for a supplier (engine)")
def get_effective_rate(
    supplier_id: int,
    product_id: Optional[int] = None,
    category_slug: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    from domains.finance.services.finance_service import get_effective_rate as _engine_rate
    result = _engine_rate(supplier_id=supplier_id, product_id=product_id,
                          category_slug=category_slug, db=db)
    return {
        "rate": float(result.applied_rate),
        "percentage": f"{float(result.applied_rate) * 100:.2f}%",
        "calculation_method": result.calculation_method,
        "supplier_rate": float(result.supplier_rate),
        "supplier_rate_source": result.supplier_rate_source,
        "base_rate": float(result.base_rate),
        "base_rate_source": result.base_rate_source,
        "product_override_rate": float(result.product_override_rate) if result.product_override_rate else None,
        "badge_level": result.badge_level,
        "category_slug": result.category_slug,
        "override_flag": result.override_flag,
    }


# === From supplier_finance.py ===
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

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from infrastructure.database.database import get_db
from domains.governance.models.user import User
from domains.finance.models.general_ledger import SupplierSettlement
from domains.finance.models.general_ledger import TransactionLedger
from domains.governance.models.admin import SupplierBankAccount
from domains.orders.models.order_entities import Order
from domains.orders.models.order_entities import OrderItem
from domains.finance.models.payments import Payout
from infrastructure.utils.dependencies import require_supplier

logger = logging.getLogger(__name__)


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


# === From supplier_finance_status.py ===
"""
Supplier Finance Router
=======================
Exposes payment-status and payout-status for each order so the supplier panel
can show which orders are paid, which payouts are completed/pending, and the
current settlement balance. See ``services.supplier.supplier_finance_service``
for the owned DB logic.
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from infrastructure.database.database import get_db
from domains.governance.models.user import User
from infrastructure.utils.dependencies import require_supplier
from domains.finance.services.country.supplier_finance_service import get_order_payment_status
from domains.finance.services.country.supplier_finance_service import get_supplier_bank_account
from domains.finance.services.country.supplier_finance_service import get_supplier_payout_summary
from domains.finance.services.country.supplier_finance_service import list_supplier_orders_with_payout_status
from domains.finance.services.country.supplier_finance_service import upsert_supplier_bank_account


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


# === From supplier_payouts.py ===
"""Supplier payouts sub-router."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from infrastructure.database.database import get_db
from infrastructure.database.schemas import PayoutOut
from domains.governance.models.user import User
from domains.suppliers.models.suppliers import SupplierProfile
from domains.finance.models.payments import Payout
from infrastructure.utils.dependencies import require_supplier

__router_prefix__ = "/supplier/payouts"


def list_payouts(current_user: User = Depends(require_supplier), db: Session = Depends(get_db)):
    supplier = db.query(SupplierProfile).filter(SupplierProfile.user_id == current_user.id).first()
    if not supplier:
        raise HTTPException(404)
    return (
        db.query(Payout)
        .filter(Payout.supplier_id == supplier.id)
        .order_by(Payout.created_at.desc())
        .all()
    )


@router.post("/request")
def request_payout(
    payload: dict,
    current_user: User = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    """Create a payout request from the supplier.

    Body:
      amount (float): Payout amount
      method (str, optional): Payment method, default "bank"
      notes (str, optional): Supplier notes
    """
    supplier = db.query(SupplierProfile).filter(SupplierProfile.user_id == current_user.id).first()
    if not supplier:
        raise HTTPException(404, "Supplier profile not found")

    amount = payload.get("amount")
    if not amount or float(amount) <= 0:
        raise HTTPException(400, "A positive payout amount is required")

    payout = Payout(
        supplier_id=supplier.id,
        amount=float(amount),
        method=payload.get("method", "bank"),
        notes=payload.get("notes", "Supplier-initiated payout request"),
        status="pending",
    )
    db.add(payout)
    db.commit()
    db.refresh(payout)
    return {"status": "success", "payout": {"id": payout.id, "amount": float(payout.amount), "status": payout.status}}


# === From supplier_payouts_pay.py ===
"""Supplier payouts sub-router."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from infrastructure.database.database import get_db
from infrastructure.database.schemas import PayoutOut
from domains.governance.models.user import User
from infrastructure.utils.dependencies import require_supplier
from domains.suppliers.services.profile.supplier_payouts_service import create_supplier_payout
from domains.finance.services.payouts.payout_batch_service import list_supplier_payouts
from domains.catalog.services.products.products_service import get_supplier_profile


@router.get("", response_model=list[PayoutOut])
def list_payouts(current_user: User = Depends(require_supplier), db: Session = Depends(get_db)):
    profile = get_supplier_profile(current_user, db)
    return list_supplier_payouts(db, profile.id)


@router.post("/request")
def request_payout(
    payload: dict,
    current_user: User = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    """Create a payout request from the supplier.

    Body:
      amount (float): Payout amount
      method (str, optional): Payment method, default "bank"
      notes (str, optional): Supplier notes
    """
    profile = get_supplier_profile(current_user, db)

    amount = payload.get("amount")
    if not amount or float(amount) <= 0:
        raise HTTPException(400, "A positive payout amount is required")

    payout = create_supplier_payout(
        db,
        profile.id,
        float(amount),
        payload.get("method", "bank"),
        payload.get("notes", "Supplier-initiated payout request"),
    )
    return {"status": "success", "payout": {"id": payout.id, "amount": float(payout.amount), "status": payout.status}}


