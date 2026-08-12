"""
Admin fallback route handlers (dashboard / stats / treasury).

Thin orchestration layer: each function validates nothing beyond what the
router already guarantees (auth dependency) and delegates the data work to
``services.admin.analytics_fallback_service``.  Keeps the HTTP contract in
the router, the business/data logic in the service.
"""
from typing import Any, Dict

from sqlalchemy.orm import Session

from routers.generated.auto_router import get

from services.admin.analytics_fallback_service import (
    get_admin_stats,
    get_commission_config,
    get_dashboard_stats,
    get_treasury_metrics,
    get_treasury_summary,
)


@get("/api/v1/admin/dashboard", deps=["db", "admin"], tags=["admin-fallback"])
def dashboard_route(db: Session, current_user=None) -> Dict[str, Any]:
    return get_dashboard_stats(db)


@get("/api/v1/admin/stats", deps=["db", "admin"], tags=["admin-fallback"])
def stats_route(db: Session, current_user=None) -> Dict[str, Any]:
    return get_admin_stats(db)


@get("/api/v1/admin/treasury", deps=["db", "admin"], tags=["admin-fallback"])
def treasury_route(db: Session, current_user=None) -> Dict[str, Any]:
    return get_treasury_summary(db)


@get("/api/v1/admin/treasury/metrics", deps=["db", "admin"], tags=["admin-fallback"])
def treasury_metrics_route(db: Session, current_user=None) -> Dict[str, Any]:
    return get_treasury_metrics(db)


@get("/api/v1/admin/commission", deps=["db", "admin"], tags=["admin-fallback"])
def commission_route(db: Session, current_user=None) -> Any:
    return get_commission_config(db)
