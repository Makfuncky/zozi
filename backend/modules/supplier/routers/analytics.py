"""Supplier analytics router — thin wrappers over the analytics + supplier domains.

Per ARCHITECTURE_DIAGRAM.md §3, module routers stay thin: auth context,
``require_feature(...)`` gate, and one service call. Endpoints use proper
Pydantic response models, paginate list endpoints, and rely on the module
prefix (no inline ``/api/v1/...`` segments).
"""

from __future__ import annotations

from typing import Any, List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from infrastructure.database.database import get_db
from infrastructure.security.dependencies import require_supplier

from rbac.dependencies import require_feature

from domains.suppliers.ports import get_supplier_analytics_summary


router = APIRouter(prefix="/supplier/analytics", tags=["supplier", "analytics"])


# ── Pydantic response schemas ────────────────────────────────────────────────


class OverviewBlock(BaseModel):
    total_products: int
    total_orders: int
    total_revenue: float
    recent_revenue: float
    average_order_value: float


class AnalyticsSummaryResponse(BaseModel):
    overview: OverviewBlock
    top_products: List[Any] = Field(default_factory=list)
    recent_orders: List[Any] = Field(default_factory=list)
    revenue_trend: List[Any] = Field(default_factory=list)


class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    page_size: int


class ProviderSummaryResponse(BaseModel):
    status: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None
    data: Optional[dict] = None


# ── Routes ───────────────────────────────────────────────────────────────────


@router.get("/summary", response_model=AnalyticsSummaryResponse)
def analytics_summary(
    current_user=Depends(require_supplier),
    db: Session = Depends(get_db),
    _: None = Depends(require_feature("analytics.read")),
):
    return get_supplier_analytics_summary(current_user, db)


@router.get("/products", response_model=PaginatedResponse)
def list_top_products(
    current_user=Depends(require_supplier),
    db: Session = Depends(get_db),
    _: None = Depends(require_feature("analytics.read")),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
):
    summary = get_supplier_analytics_summary(current_user, db)
    items = list(summary.get("top_products", []) or [])
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "items": items[start:end],
        "total": len(items),
        "page": page,
        "page_size": page_size,
    }


@router.get("/orders", response_model=PaginatedResponse)
def list_recent_orders(
    current_user=Depends(require_supplier),
    db: Session = Depends(get_db),
    _: None = Depends(require_feature("analytics.reports.read")),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
):
    summary = get_supplier_analytics_summary(current_user, db)
    items = list(summary.get("recent_orders", []) or [])
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "items": items[start:end],
        "total": len(items),
        "page": page,
        "page_size": page_size,
    }


@router.get("/revenue-trend", response_model=PaginatedResponse)
def get_revenue_trend(
    current_user=Depends(require_supplier),
    db: Session = Depends(get_db),
    _: None = Depends(require_feature("analytics.reports.read")),
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=365),
):
    summary = get_supplier_analytics_summary(current_user, db)
    items = list(summary.get("revenue_trend", []) or [])
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "items": items[start:end],
        "total": len(items),
        "page": page,
        "page_size": page_size,
    }


@router.get("/provider/summary", response_model=ProviderSummaryResponse)
def get_provider_summary(
    current_user=Depends(require_supplier),
    _: None = Depends(require_feature("analytics.dashboard.view")),
    country_code: Optional[str] = Query(None),
    period: str = Query("30d"),
):
    from domains.analytics.services.dashboards.analytics_service import (
        get_analytics_summary as _provider_summary,
    )
    return _provider_summary(country_code=country_code, period=period)
