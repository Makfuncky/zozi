"""Admin analytics router — thin wrappers over the analytics domain services.

Per ARCHITECTURE_DIAGRAM.md §3, module routers stay thin: auth context,
``require_feature(...)`` gate, and one service call. The analytics services
live in ``domains.analytics.services``.

Routers MUST NOT do DB writes, business logic, or embed ``/api/v1/...`` in
path strings (the module prefix is applied by ``main.py``).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from infrastructure.database.database import get_db
from infrastructure.security.dependencies import require_admin

from rbac.dependencies import require_feature

from domains.analytics.services.dashboards.admin_dashboard_service import (
    admin_dashboard_fallback,
    admin_stats_fallback,
    admin_payouts_fallback,
    admin_commission_fallback,
    admin_employees_fallback,
    admin_payments_fallback,
    admin_logistics_fallback,
    admin_logistics_partners_fallback,
    admin_treasury_fallback,
    admin_treasury_metrics_fallback,
)
from domains.analytics.services.dashboards.analytics_service import (
    get_analytics as _get_analytics_overview,
    get_customer_insights as _get_customer_insights,
    get_analytics_timeseries as _get_analytics_timeseries,
    get_top_products_analytics as _get_top_products_analytics,
    get_user_growth_analytics as _get_user_growth_analytics,
    get_chatbot_analytics as _get_chatbot_analytics,
    get_analytics_summary as _get_analytics_summary_provider,
    refresh_admin_analytics_snapshots as _refresh_analytics_snapshots,
)
from domains.analytics.services.aggregation.command_center_service import (
    CommandCenterService,
)

router = APIRouter(prefix="/admin/analytics", tags=["admin", "analytics"])


@router.get("/health")
def health(_: dict = Depends(require_admin)):
    return {"status": "ok", "router": "admin_analytics", "prefix": "/admin/analytics"}


@router.get("/summary")
def get_dashboard_summary(
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
    __: None = Depends(require_feature("analytics.dashboard.view")),
):
    return admin_dashboard_fallback(db)


@router.get("/stats")
def get_stats(
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
    __: None = Depends(require_feature("analytics.read")),
):
    return admin_stats_fallback(db)


@router.get("/payouts")
def get_payouts(
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
    __: None = Depends(require_feature("analytics.reports.read")),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
):
    return admin_payouts_fallback(db, page=page, page_size=page_size)


@router.get("/commission")
def get_commission(
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
    __: None = Depends(require_feature("analytics.reports.read")),
):
    return admin_commission_fallback(db)


@router.get("/employees")
def get_employees(
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
    __: None = Depends(require_feature("analytics.reports.read")),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
):
    return admin_employees_fallback(db, page=page, page_size=page_size)


@router.get("/payments")
def get_payments(
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
    __: None = Depends(require_feature("analytics.reports.read")),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
):
    return admin_payments_fallback(db, page=page, page_size=page_size)


@router.get("/logistics")
def get_logistics(
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
    __: None = Depends(require_feature("analytics.read")),
):
    return admin_logistics_fallback(db)


@router.get("/logistics/partners")
def get_logistics_partners(
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
    __: None = Depends(require_feature("analytics.read")),
):
    return admin_logistics_partners_fallback(db)


@router.get("/treasury")
def get_treasury(
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
    __: None = Depends(require_feature("analytics.reports.read")),
):
    return admin_treasury_fallback(db)


@router.get("/treasury/metrics")
def get_treasury_metrics(
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
    __: None = Depends(require_feature("analytics.reports.read")),
):
    return admin_treasury_metrics_fallback(db)


@router.get("/overview")
def get_overview(
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
    __: None = Depends(require_feature("analytics.dashboard.view")),
):
    return _get_analytics_overview(db)


@router.get("/customer-insights")
def get_customer_insights(
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
    __: None = Depends(require_feature("analytics.reports.read")),
):
    return _get_customer_insights(db)


@router.get("/timeseries")
def get_timeseries(
    period: str = Query("30d", pattern="^(7d|30d|90d)$"),
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
    __: None = Depends(require_feature("analytics.dashboard.view")),
):
    return _get_analytics_timeseries(period, db)


@router.get("/top-products")
def get_top_products(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
    __: None = Depends(require_feature("analytics.reports.read")),
):
    return _get_top_products_analytics(limit, db)


@router.get("/user-growth")
def get_user_growth(
    period: str = Query("30d", pattern="^(7d|30d|90d)$"),
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
    __: None = Depends(require_feature("analytics.reports.read")),
):
    return _get_user_growth_analytics(period, db)


@router.get("/chatbot")
def get_chatbot_analytics(
    period: str = Query("30d", pattern="^(7d|30d|90d)$"),
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
    __: None = Depends(require_feature("analytics.reports.read")),
):
    return _get_chatbot_analytics(period, db)


@router.get("/provider/summary")
def get_provider_summary(
    _: dict = Depends(require_admin),
    __: None = Depends(require_feature("analytics.dashboard.view")),
    country_code: Optional[str] = Query(None),
    period: str = Query("30d"),
):
    return _get_analytics_summary_provider(country_code=country_code, period=period)


@router.post("/snapshots/refresh", status_code=200)
def refresh_snapshots(
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
    __: None = Depends(require_feature("analytics.reports.export")),
):
    return _refresh_analytics_snapshots(db)


@router.get("/command-center/stats")
def get_command_center_stats(
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
    __: None = Depends(require_feature("analytics.dashboard.view")),
):
    return CommandCenterService(db).get_comprehensive_stats()


@router.get("/command-center/treasury")
def get_command_center_treasury(
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
    __: None = Depends(require_feature("analytics.reports.read")),
):
    return CommandCenterService(db).get_treasury_metrics()


@router.get("/command-center/workforce")
def get_command_center_workforce(
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
    __: None = Depends(require_feature("analytics.reports.read")),
):
    return CommandCenterService(db).get_workforce_metrics()


@router.get("/command-center/external-intelligence")
def get_command_center_external_intelligence(
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
    __: None = Depends(require_feature("analytics.reports.read")),
):
    return CommandCenterService(db).get_external_intelligence()


@router.get("/command-center/system-health")
def get_command_center_system_health(
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
    __: None = Depends(require_feature("analytics.dashboard.view")),
):
    return CommandCenterService(db).get_system_health_dashboard()


@router.get("/command-center/fraud-war-map")
def get_command_center_fraud_war_map(
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
    __: None = Depends(require_feature("analytics.reports.read")),
):
    return CommandCenterService(db).get_fraud_war_map()
