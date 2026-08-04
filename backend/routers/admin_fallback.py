"""
Admin Fallback Router — non-country-scoped route aliases.

The dedicated admin_*.py routers define routes WITH a {country_code} path
parameter (e.g. GET /{code}/suppliers).  The admin frontend often hits
the SAME endpoints WITHOUT a country code (GET /admin/suppliers).

This router provides shallow proxy routes that delegate to the same
underlying controllers / service layer, so the frontend works whether or
not a country code is supplied.  All data access goes through
services/core/admin_dashboard_service.py (LC1: routers stay thin).
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from data.db import get_db
from data.schemas import CursorPage
from utils.pagination import cursor_paginate_desc
from data.controllers_admin_controller import (
    get_current_admin,
    get_all_suppliers,
)
from services.core.admin_dashboard_service import (
    get_fallback_admin_dashboard_stats,
    get_fallback_admin_stats,
    list_payouts_query,
    list_categories_query,
    list_payments_query,
    list_accounts_fallback,
    list_employees_query,
    get_commission_config,
    list_shipping_carriers_fallback,
    get_shipping_zone_count,
    get_shipment_count,
    get_accounting_summary,
    get_treasury_cash_total,
)

router = APIRouter()


# ── Dashboard (fallback when no country code is given) ────────────────────

@router.get("/dashboard")
def admin_dashboard_fallback(
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """Simple admin dashboard stats — works without country_code."""
    return get_fallback_admin_dashboard_stats(db)


# ── Stats (simple aggregate) ──────────────────────────────────────────────

@router.get("/stats")
def admin_stats_fallback(
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """Simple aggregate stats — works without country_code."""
    return get_fallback_admin_stats(db)


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
    return cursor_paginate_desc(
        list_payouts_query(db), cursor=cursor, page_size=limit
    )


# ── Categories (fallback) ──────────────────────────────────────────────────

@router.get("/categories", response_model=CursorPage)
def admin_categories_fallback(
    cursor: str | None = Query(None, description="Cursor for next page"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """List all categories (no country code required)."""
    return cursor_paginate_desc(
        list_categories_query(db), cursor=cursor, page_size=limit
    )


# ── Commission (fallback) ──────────────────────────────────────────────────

@router.get("/commission")
def admin_commission_fallback(
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """Get commission global config (no country code required)."""
    config = get_commission_config(db)
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
    return cursor_paginate_desc(
        list_employees_query(db), cursor=cursor, page_size=limit
    )


# ── Payments (fallback) ────────────────────────────────────────────────────

@router.get("/payments", response_model=CursorPage)
def admin_payments_fallback(
    cursor: str | None = Query(None, description="Cursor for next page"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """List all payments (no country code required)."""
    return cursor_paginate_desc(
        list_payments_query(db), cursor=cursor, page_size=limit
    )


# ── Logistics (fallback — list shipping carriers) ──────────────────────────

@router.get("/logistics")
def admin_logistics_fallback(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """List logistics carriers and partners (no country code required)."""
    carriers = list_shipping_carriers_fallback(db, active_only=True)
    return {
        "active_carriers": [
            {"id": c.id, "name": c.name, "code": c.code}
            for c in carriers[skip : skip + limit]
        ],
        "active_zones": get_shipping_zone_count(db),
        "total_shipments": get_shipment_count(db),
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
    carriers = list_shipping_carriers_fallback(db, active_only=True)
    return {
        "partners": [
            {"id": c.id, "name": c.name, "code": c.code, "is_active": c.is_active}
            for c in carriers[skip : skip + limit]
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
    return {
        "total_cash": get_treasury_cash_total(db),
        "total_accounts": get_accounting_summary(db)["total_accounts"],
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
    accounts = list_accounts_fallback(db, skip=skip, limit=limit)
    return {
        "total_accounts": len(accounts),
        "total_cash": get_treasury_cash_total(db),
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
