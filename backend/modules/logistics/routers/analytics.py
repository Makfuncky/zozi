"""Logistics analytics router — thin wrappers over the analytics + logistics domains.

Per ARCHITECTURE_DIAGRAM.md §3, module routers stay thin: auth context,
``require_feature(...)`` gate, and one service call. Logistics-partner-facing
analytics covers delivery performance and shipment analytics for the partner's
own scope.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from infrastructure.database.database import get_db
from infrastructure.security.dependencies import get_current_user, require_logistics

from rbac.dependencies import require_feature

from domains.analytics.services.dashboards.analytics_service import (
    get_analytics_summary as _get_analytics_summary_provider,
)


router = APIRouter(prefix="/logistics/analytics", tags=["logistics", "analytics"])


def _current_partner_id(current_user: dict) -> int:
    return int(current_user.get("user_id") or current_user.get("id") or 0)


@router.get("/health")
def health(_: dict = Depends(require_logistics)):
    return {"status": "ok", "router": "logistics_analytics"}


@router.get("/summary")
def get_my_summary(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(require_feature("analytics.dashboard.view")),
):
    partner_id = _current_partner_id(current_user)
    return {
        "partner_id": partner_id,
        "scope": "self",
        "metrics_available_at": "/logistics/analytics/delivery-performance",
    }


@router.get("/delivery-performance")
def get_delivery_performance(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(require_feature("analytics.read")),
    period: str = Query("30d", pattern="^(7d|30d|90d)$"),
):
    partner_id = _current_partner_id(current_user)
    return {
        "partner_id": partner_id,
        "period": period,
        "on_time_rate": 0.0,
        "avg_delivery_hours": 0.0,
        "failed_shipments": 0,
    }


@router.get("/shipments")
def get_shipment_analytics(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(require_feature("analytics.reports.read")),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    status: str | None = Query(None),
):
    partner_id = _current_partner_id(current_user)
    return {
        "partner_id": partner_id,
        "page": page,
        "page_size": page_size,
        "items": [],
        "total": 0,
        "filter_status": status,
    }


@router.get("/provider/summary")
def get_provider_summary(
    current_user: dict = Depends(get_current_user),
    _: None = Depends(require_feature("analytics.dashboard.view")),
    country_code: str | None = Query(None),
    period: str = Query("30d"),
):
    return _get_analytics_summary_provider(country_code=country_code, period=period)
