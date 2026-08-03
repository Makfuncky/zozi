"""
Admin Fallback Router — non-country-scoped route aliases.

The dedicated admin_*.py routers define routes WITH a {country_code} path
parameter (e.g. GET /{code}/suppliers).  The admin frontend often hits
the SAME endpoints WITHOUT a country code (GET /admin/suppliers).

This router provides shallow proxy routes that delegate to the same
underlying controllers, so the frontend works whether or not a country
code is supplied.
"""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from data.db import get_db
from data.schemas import CursorPage
from utils.pagination import cursor_paginate_desc
from data.controllers_admin_controller import (
    get_current_admin,
    get_all_suppliers,
    list_pending_payouts,
)
from data.models import (
    Category as CategoryModel,
    CommissionGlobalConfig,
    Employee,
    Payment,
    Payout as PayoutModel,
    ShippingCarrier,
    Shipment,
    ShippingZone,
)

router = APIRouter()


# ── Dashboard (fallback when no country code is given) ────────────────────

@router.get("/dashboard")
def admin_dashboard_fallback(
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """Simple admin dashboard stats — works without country_code."""
    from sqlalchemy import func as sqlfunc
    from data.models import User as UserModel, Order as OrderModel, Product as ProductModel

    total_revenue = (
        db.query(sqlfunc.sum(Payment.amount))
        .filter(Payment.status == "completed")
        .scalar()
        or 0
    )
    total_users = db.query(sqlfunc.count(UserModel.id)).scalar() or 0
    total_orders = db.query(sqlfunc.count(OrderModel.id)).scalar() or 0

    return {
        "total_revenue": float(total_revenue),
        "total_users": total_users,
        "total_orders": total_orders,
        "active_sessions": 0,
        "pending_payouts": db.query(PayoutModel).filter(
            PayoutModel.status == "pending"
        ).count(),
    }


# ── Stats (simple aggregate) ──────────────────────────────────────────────

@router.get("/stats")
def admin_stats_fallback(
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """Simple aggregate stats — works without country_code."""
    from sqlalchemy import func as sqlfunc
    from data.models import User as UserModel, Order as OrderModel, Product as ProductModel

    return {
        "total_users": db.query(sqlfunc.count(UserModel.id)).scalar() or 0,
        "total_customers": db.query(sqlfunc.count(UserModel.id)).filter(
            UserModel.role == "customer"
        ).scalar() or 0,
        "total_suppliers": db.query(sqlfunc.count(UserModel.id)).filter(
            UserModel.role == "supplier"
        ).scalar() or 0,
        "total_orders": db.query(sqlfunc.count(OrderModel.id)).scalar() or 0,
        "total_products": db.query(sqlfunc.count(ProductModel.id)).filter(
            ProductModel.is_deleted == False
        ).scalar() or 0,
        "pending_payouts": db.query(PayoutModel).filter(
            PayoutModel.status == "pending"
        ).count(),
    }


# ── Suppliers (fallback — delegates to get_all_suppliers) ─────────────────

@router.get("/suppliers")
def admin_suppliers_fallback(
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
    q: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    badge: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """List all suppliers (no country code required)."""
    return get_all_suppliers(
        db,
        skip=(page - 1) * page_size,
        limit=page_size,
        q=q,
        status=status,
        badge=badge,
    )


# ── Payouts (fallback) ────────────────────────────────────────────────────

@router.get("/payouts", response_model=CursorPage)
def admin_payouts_fallback(
    cursor: str | None = Query(None, description="Cursor for next page"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """List all payouts (no country code required)."""
    q = db.query(PayoutModel).order_by(PayoutModel.id.desc())
    return cursor_paginate_desc(q, cursor=cursor, page_size=limit)


# ── Categories (fallback) ──────────────────────────────────────────────────

@router.get("/categories", response_model=CursorPage)
def admin_categories_fallback(
    cursor: str | None = Query(None, description="Cursor for next page"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """List all categories (no country code required)."""
    q = db.query(CategoryModel).order_by(CategoryModel.id.desc())
    return cursor_paginate_desc(q, cursor=cursor, page_size=limit)


# ── Commission (fallback) ──────────────────────────────────────────────────

@router.get("/commission")
def admin_commission_fallback(
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """Get commission global config (no country code required)."""
    config = db.query(CommissionGlobalConfig).first()
    return config or {}


# ── Employees (fallback) ───────────────────────────────────────────────────

@router.get("/employees", response_model=CursorPage)
def admin_employees_fallback(
    cursor: str | None = Query(None, description="Cursor for next page"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """List all employees (no country code required)."""
    from data.models import User as UserModel
    q = (
        db.query(Employee)
        .join(UserModel, Employee.user_id == UserModel.id)
        .order_by(UserModel.full_name.asc().nullslast(), Employee.id)
    )
    return cursor_paginate_desc(q, cursor=cursor, page_size=limit)


# ── Payments (fallback) ────────────────────────────────────────────────────

@router.get("/payments", response_model=CursorPage)
def admin_payments_fallback(
    cursor: str | None = Query(None, description="Cursor for next page"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """List all payments (no country code required)."""
    q = db.query(Payment).order_by(Payment.id.desc())
    return cursor_paginate_desc(q, cursor=cursor, page_size=limit)


# ── Logistics (fallback — list shipping carriers) ──────────────────────────

@router.get("/logistics")
def admin_logistics_fallback(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """List logistics carriers and partners (no country code required)."""
    from data.models import Shipment, ShippingZone

    carriers = db.query(ShippingCarrier).filter(
        ShippingCarrier.is_active == True
    ).offset(skip).limit(limit).all()
    zone_count = db.query(ShippingZone).filter(
        ShippingZone.is_active == True
    ).count()
    shipment_count = db.query(Shipment).count()

    return {
        "active_carriers": [
            {"id": c.id, "name": c.name, "code": c.code}
            for c in carriers
        ],
        "active_zones": zone_count,
        "total_shipments": shipment_count,
    }
# ── Logistics Partners (fallback) ──────────────────────────────────────────────

@router.get("/logistics-partners")
def admin_logistics_partners_fallback(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """List logistics partners (no country code required)."""
    carriers = db.query(ShippingCarrier).filter(
        ShippingCarrier.is_active == True
    ).offset(skip).limit(limit).all()
    return {
        "partners": [
            {"id": c.id, "name": c.name, "code": c.code, "is_active": c.is_active}
            for c in carriers
        ],
        "total": len(carriers),
    }


# ── Treasury (bare fallback — returns summary) ────────────────────────────────

@router.get("/treasury")
def admin_treasury_fallback(
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """Treasury summary — redirect to /admin/treasury/metrics if you need full metrics."""
    from data.models import Account as AccountModel, AccountBalance as AccountBalanceModel

    total_cash = (
        db.query(func.sum(AccountBalanceModel.balance))
        .select_from(AccountBalanceModel)
        .scalar()
        or 0
    )
    account_count = db.query(AccountModel).count()

    return {
        "total_cash": float(total_cash),
        "total_accounts": account_count,
        "metrics_available_at": "/admin/treasury/metrics",
    }


# ── Treasury Metrics (fallback — forward to existing admin_treasury logic) ─

@router.get("/treasury/metrics")
def admin_treasury_metrics_fallback(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """Treasury metrics summary (no country code required)."""
    from data.models import Account as AccountModel, AccountBalance as AccountBalanceModel

    accounts = db.query(AccountModel).offset(skip).limit(limit).all()
    total_cash = (
        db.query(func.sum(AccountBalanceModel.balance))
        .select_from(AccountBalanceModel)
        .scalar()
        or 0
    )

    return {
        "total_accounts": len(accounts),
        "total_cash": float(total_cash),
        "accounts": [
            {
                "id": a.id,
                "name": a.name,
                "type": a.type,
                "currency": a.currency,
            }
            for a in accounts
        ],
    }
