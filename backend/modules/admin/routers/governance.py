"""Admin governance router — thin HTTP layer delegating to governance domain services."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from infrastructure.database.database import get_db
from infrastructure.security.dependencies import require_admin
from infrastructure.utils.config import settings
from rbac.dependencies import require_feature
from domains.governance.services.command_center.command_center_service import (
    create_executive_news,
    delete_executive_news,
    get_alerts,
    get_command_center,
    get_command_center_headlines,
    get_command_center_heartbeat,
    get_comprehensive_dashboard,
    get_dashboard,
    get_dashboard_stats,
    get_executive_news,
    get_fraud_alerts,
    get_realtime_metrics,
    get_system_metrics,
    get_treasury_metrics,
    resolve_alert,
)

router = APIRouter(tags=["admin", "governance"])


@router.get("/api/v1/admin/governance/config/checkout")
def get_checkout_config(
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("governance.system.health")),
):
    return {
        "vat_rate": settings.checkout_vat_rate,
        "shipping_flat_rate": settings.checkout_shipping_flat_rate,
        "free_shipping_threshold": settings.checkout_free_shipping_threshold,
    }


# ── Command center (moved from modules/admin/routers/command_center.py) ────────


@router.get("/api/v1/admin/command-center/heartbeat")
def heartbeat_route(
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("governance.system.health")),
):
    return get_command_center_heartbeat(db=db)


@router.get("/api/v1/admin/command-center/system-metrics")
def system_metrics_route(
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("governance.system.health")),
):
    return get_system_metrics(db=db)


@router.get("/api/v1/admin/command-center/treasury-metrics")
def treasury_metrics_route(
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("governance.treasury.read")),
):
    return get_treasury_metrics(db=db)


@router.get("/api/v1/admin/command-center/dashboard")
def dashboard_route(
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("governance.analytics.read")),
):
    return get_dashboard(current_user=current_user, db=db)


@router.get("/api/v1/admin/command-center/fraud-alerts")
def fraud_alerts_route(
    limit: int = Query(50),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("governance.fraud.read")),
):
    return get_fraud_alerts(limit=limit, db=db)


@router.get("/api/v1/admin/command-center/news")
def news_route(
    limit: int = Query(20),
    category: str | None = None,
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("governance.analytics.read")),
):
    return get_executive_news(limit=limit, category=category, db=db)


@router.get("/api/v1/admin/command-center/headlines")
def headlines_route(
    limit: int = Query(20),
    category: str | None = None,
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("governance.analytics.read")),
):
    return get_command_center_headlines(limit=limit, category=category, db=db)


@router.post("/api/v1/admin/command-center/news", status_code=201)
def create_news_route(
    payload: dict | None = None,
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("governance.analytics.read")),
):
    return create_executive_news(payload=payload, db=db)


@router.delete("/api/v1/admin/command-center/news/{news_id}")
def delete_news_route(
    news_id: int,
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("governance.analytics.read")),
):
    return delete_executive_news(news_id=news_id, db=db)


@router.get("/api/v1/admin/command-center/alerts")
def alerts_route(
    severity: str | None = None,
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("governance.security.incident.read")),
):
    return get_alerts(severity=severity, db=db)


@router.post("/api/v1/admin/command-center/alerts/{alert_id}/resolve")
def resolve_alert_route(
    alert_id: int,
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("governance.security.incident.manage")),
):
    return resolve_alert(alert_id=alert_id, db=db)


@router.get("/api/v1/admin/command-center/dashboard-stats")
def dashboard_stats_route(
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("governance.analytics.read")),
):
    return get_dashboard_stats(current_user=current_user, db=db)


@router.get("/api/v1/admin/command-center/realtime-metrics")
def realtime_metrics_route(
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("governance.system.health")),
):
    return get_realtime_metrics(db=db)


@router.get("/api/v1/admin/command-center/comprehensive-dashboard")
def comprehensive_dashboard_route(
    current_user: dict = Depends(require_admin),
    country_code: str | None = None,
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("governance.analytics.read")),
):
    return get_comprehensive_dashboard(current_user=current_user, db=db, country_code=country_code)


@router.get("/api/v1/admin/command-center/")
def command_center_root_route(
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("governance.analytics.read")),
):
    return get_command_center(db=db)
