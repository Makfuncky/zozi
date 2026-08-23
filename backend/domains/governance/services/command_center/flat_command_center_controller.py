"""Command-center controller (CONTROLLERS layer).

Wraps ``services.governance.command_center_service`` and exposes the
administrative command-center endpoints under ``/api/v1/admin/command-center``.

HTTP contract declared with ``infrastructure.routing.route_contract`` decorators so the
router can be auto-generated; the thin hand-written ``routers/command_center_controller.py``
is retained as the authoritative router (the generator collision-skips these paths).
"""
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from infrastructure.routing.route_contract import delete, get, post

from domains.governance.services.command_center_service import create_executive_news
from domains.governance.services.command_center_service import delete_executive_news
from domains.governance.services.command_center_service import get_alerts
from domains.governance.services.command_center_service import get_command_center
from domains.governance.services.command_center_service import get_command_center_headlines
from domains.governance.services.command_center_service import get_comprehensive_dashboard
from domains.governance.services.command_center_service import get_dashboard
from domains.governance.services.command_center_service import get_dashboard_stats
from domains.governance.services.command_center_service import get_executive_news
from domains.governance.services.command_center_service import get_fraud_alerts
from domains.governance.services.command_center_service import get_realtime_metrics
from domains.governance.services.command_center_service import get_system_metrics
from domains.governance.services.command_center_service import get_treasury_metrics
from domains.governance.services.command_center_service import get_command_center_heartbeat
from domains.governance.services.command_center_service import resolve_alert


@get("/api/v1/admin/command-center/heartbeat", deps=["db"], tags=["command-center"])
def heartbeat_route(db: Session = None):
    return get_command_center_heartbeat(db=db)


@get("/api/v1/admin/command-center/system-metrics", deps=["db"], tags=["command-center"])
def system_metrics_route(db: Session = None):
    return get_system_metrics(db=db)


@get("/api/v1/admin/command-center/treasury-metrics", deps=["db"], tags=["command-center"])
def treasury_metrics_route(db: Session = None):
    return get_treasury_metrics(db=db)


@get("/api/v1/admin/command-center/dashboard", deps=["db", "admin"], tags=["command-center"])
def dashboard_route(current_user=None, db: Session = None):
    return get_dashboard(current_user=current_user, db=db)


@get(
    "/api/v1/admin/command-center/fraud-alerts",
    deps=["db"],
    query=["limit"],
    tags=["command-center"],
)
def fraud_alerts_route(limit: int = 50, db: Session = None):
    return get_fraud_alerts(limit=limit, db=db)


@get(
    "/api/v1/admin/command-center/news",
    deps=["db"],
    query=["limit", "category"],
    tags=["command-center"],
)
def news_route(limit: int = 20, category: str = None, db: Session = None):
    return get_executive_news(limit=limit, category=category, db=db)


@get(
    "/api/v1/admin/command-center/headlines",
    deps=["db"],
    query=["limit", "category"],
    tags=["command-center"],
)
def headlines_route(limit: int = 20, category: str = None, db: Session = None):
    return get_command_center_headlines(limit=limit, category=category, db=db)


@post(
    "/api/v1/admin/command-center/news",
    deps=["db"],
    body=Any,
    status_code=201,
    tags=["command-center"],
)
def create_news_route(payload: dict = None, db: Session = None):
    return create_executive_news(payload=payload, db=db)


@delete("/api/v1/admin/command-center/news/{news_id}", deps=["db"], tags=["command-center"])
def delete_news_route(news_id: int, db: Session = None):
    return delete_executive_news(news_id=news_id, db=db)


@get(
    "/api/v1/admin/command-center/alerts",
    deps=["db"],
    query=["severity"],
    tags=["command-center"],
)
def alerts_route(severity: str = None, db: Session = None):
    return get_alerts(severity=severity, db=db)


@post(
    "/api/v1/admin/command-center/alerts/{alert_id}/resolve",
    deps=["db"],
    status_code=200,
    tags=["command-center"],
)
def resolve_alert_route(alert_id: int, db: Session = None):
    return resolve_alert(alert_id=alert_id, db=db)


@get("/api/v1/admin/command-center/dashboard-stats", deps=["db", "admin"], tags=["command-center"])
def dashboard_stats_route(current_user=None, db: Session = None):
    return get_dashboard_stats(current_user=current_user, db=db)


@get("/api/v1/admin/command-center/realtime-metrics", deps=["db"], tags=["command-center"])
def realtime_metrics_route(db: Session = None):
    return get_realtime_metrics(db=db)


@get(
    "/api/v1/admin/command-center/comprehensive-dashboard",
    deps=["db", "admin"],
    query=["country_code"],
    tags=["command-center"],
)
def comprehensive_dashboard_route(current_user=None, country_code: str = None, db: Session = None):
    return get_comprehensive_dashboard(current_user=current_user, db=db, country_code=country_code)


@get("/api/v1/admin/command-center/", deps=["db"], tags=["command-center"])
def command_center_root_route(db: Session = None):
    return get_command_center(db=db)
