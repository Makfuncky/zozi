"""
Admin Fallback Router — non-country-scoped route aliases.

The dedicated admin_*.py routers define routes WITH a {country_code} path
parameter (e.g. GET /{code}/suppliers).  The admin frontend often hits
the SAME endpoints WITHOUT a country code (GET /admin/suppliers).

This router provides shallow proxy routes that delegate to the same
underlying controllers, so the frontend works whether or not a country
code is supplied.
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from controllers.admin.admin_controller import (
    get_all_suppliers,
    get_current_admin,
)
from db.database import get_db
from _legacy.models import Category as CategoryModel
from _legacy.models import (
    CommissionGlobalConfig,
    Employee,
    Payment,
    Product as ProductModel,
    Shipment,
    ShippingCarrier,
    ShippingZone,
)
from _legacy.models import Payout as PayoutModel
from _legacy.models import User as UserModel
from services.common.db_read import (
    all_rows,
    count,
    first,
    scalar,
    scalar_sum,
    scalar_with_filters,
)
import structlog
logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/admin")


# ── Dashboard (fallback when no country code is given) ────────────────────

@router.get("/dashboard", response_model=dict)
def admin_dashboard_fallback(
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """Simple admin dashboard stats — works without country_code."""
    total_revenue = scalar_sum(db, Payment.amount, [Payment.status == "completed"])
    total_users = scalar_with_filters(db, func.count(UserModel.id)) or 0
    total_orders = scalar_with_filters(db, func.count(UserModel.id)) or 0

    return {
        "total_revenue": float(total_revenue),
        "total_users": total_users,
        "total_orders": total_orders,
        "active_sessions": 0,
        "pending_payouts": count(db, PayoutModel, [PayoutModel.status == "pending"]),
    }


# ── Stats (simple aggregate) ──────────────────────────────────────────────

@router.get("/stats", response_model=dict)
def admin_stats_fallback(
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """Simple aggregate stats — works without country_code."""
    return {
        "total_users": scalar_with_filters(db, func.count(UserModel.id)) or 0,
        "total_customers": scalar_with_filters(
            db, func.count(UserModel.id), [UserModel.role == "customer"]
        )
        or 0,
        "total_suppliers": scalar_with_filters(
            db, func.count(UserModel.id), [UserModel.role == "supplier"]
        )
        or 0,
        "total_orders": scalar_with_filters(db, func.count(UserModel.id)) or 0,
        "total_products": scalar_with_filters(
            db, func.count(ProductModel.id), [ProductModel.is_deleted == False]
        )
        or 0,
        "pending_payouts": count(db, PayoutModel, [PayoutModel.status == "pending"]),
    }


# ── Suppliers (fallback — delegates to get_all_suppliers) ─────────────────

@router.get("/suppliers", response_model=dict)
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

@router.get("/payouts", response_model=dict)
def admin_payouts_fallback(
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """List all payouts (no country code required)."""
    skip = (page - 1) * page_size
    items = all_rows(
        db,
        PayoutModel,
        order_by=PayoutModel.created_at.desc(),
        offset=skip,
        limit=page_size,
    )
    total = count(db, PayoutModel)
    return {"items": items, "total": total, "page": page, "page_size": page_size}


# ── Categories (fallback) ──────────────────────────────────────────────────

@router.get("/categories", response_model=dict)
def admin_categories_fallback(
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """List all categories (no country code required)."""
    skip = (page - 1) * page_size
    items = all_rows(
        db,
        CategoryModel,
        order_by=CategoryModel.name,
        offset=skip,
        limit=page_size,
    )
    total = count(db, CategoryModel)
    return {"items": items, "total": total, "page": page, "page_size": page_size}


# ── Commission (fallback) ──────────────────────────────────────────────────

@router.get("/commission", response_model=dict)
def admin_commission_fallback(
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """Get commission global config (no country code required)."""
    config = first(db, CommissionGlobalConfig)
    return config or {}


# ── Employees (fallback) ───────────────────────────────────────────────────

@router.get("/employees", response_model=dict)
def admin_employees_fallback(
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """List all employees (no country code required)."""
    skip = (page - 1) * page_size
    items = all_rows(
        db,
        Employee,
        joins=[(UserModel, Employee.user_id == UserModel.id)],
        order_by=UserModel.full_name.asc().nullslast(),
        offset=skip,
        limit=page_size,
    )
    total = count(db, Employee)
    return {"items": items, "total": total, "page": page, "page_size": page_size}


# ── Payments (fallback) ────────────────────────────────────────────────────

@router.get("/payments", response_model=dict)
def admin_payments_fallback(
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """List all payments (no country code required)."""
    skip = (page - 1) * page_size
    items = all_rows(
        db,
        Payment,
        order_by=Payment.created_at.desc(),
        offset=skip,
        limit=page_size,
    )
    total = count(db, Payment)
    return {"items": items, "total": total, "page": page, "page_size": page_size}


# ── Logistics (fallback — list shipping carriers) ──────────────────────────

@router.get("/logistics", response_model=dict)
def admin_logistics_fallback(
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """List logistics carriers and partners (no country code required)."""
    carriers = all_rows(db, ShippingCarrier, [ShippingCarrier.is_active == True])
    zone_count = count(db, ShippingZone, [ShippingZone.is_active == True])
    shipment_count = count(db, Shipment)

    return {
        "active_carriers": [
            {"id": c.id, "name": c.name, "code": c.code}
            for c in carriers
        ],
        "active_zones": zone_count,
        "total_shipments": shipment_count,
    }


# ── Logistics Partners (fallback) ──────────────────────────────────────────────

@router.get("/logistics-partners", response_model=dict)
def admin_logistics_partners_fallback(
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """List logistics partners (no country code required)."""
    carriers = all_rows(db, ShippingCarrier, [ShippingCarrier.is_active == True])
    return {
        "partners": [
            {"id": c.id, "name": c.name, "code": c.code, "is_active": c.is_active}
            for c in carriers
        ],
        "total": len(carriers),
    }


# ── Treasury (bare fallback — returns summary) ────────────────────────────────

@router.get("/treasury", response_model=dict)
def admin_treasury_fallback(
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """Treasury summary — redirect to /admin/treasury/metrics if you need full metrics."""
    from _legacy.models import Account as AccountModel
    from _legacy.models import AccountBalance as AccountBalanceModel

    total_cash = (
        scalar(
            db,
            select(func.sum(AccountBalanceModel.balance)).select_from(
                AccountBalanceModel
            ),
        )
        or 0
    )
    account_count = count(db, AccountModel)

    return {
        "total_cash": float(total_cash),
        "total_accounts": account_count,
        "metrics_available_at": "/admin/treasury/metrics",
    }


# ── Treasury Metrics (fallback — forward to existing admin_treasury logic) ─

@router.get("/treasury/metrics", response_model=dict)
def admin_treasury_metrics_fallback(
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """Treasury metrics summary (no country code required)."""
    from _legacy.models import Account as AccountModel
    from _legacy.models import AccountBalance as AccountBalanceModel

    accounts = all_rows(db, AccountModel)
    total_cash = (
        scalar(
            db,
            select(func.sum(AccountBalanceModel.balance)).select_from(
                AccountBalanceModel
            ),
        )
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
