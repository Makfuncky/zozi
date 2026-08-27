"""Employee analytics router — thin wrappers over the analytics + HR domains.

Per ARCHITECTURE_DIAGRAM.md §3, module routers stay thin: auth context,
``require_feature(...)`` gate, and one service call. Employee-facing analytics
covers personal performance, team aggregates, and OKR progress.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from infrastructure.database.database import get_db
from infrastructure.security.dependencies import get_current_user, require_employee

from rbac.dependencies import require_feature

from domains.analytics.services.dashboards.analytics_service import (
    get_analytics_summary as _get_analytics_summary_provider,
)


router = APIRouter(prefix="/employee/analytics", tags=["employee", "analytics"])


def _current_user_id(current_user: dict) -> int:
    return int(current_user.get("user_id") or current_user.get("id") or 0)


@router.get("/health")
def health(_: dict = Depends(require_employee)):
    return {"status": "ok", "router": "employee_analytics"}


@router.get("/summary")
def get_my_summary(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(require_feature("analytics.dashboard.view")),
):
    user_id = _current_user_id(current_user)
    return {
        "user_id": user_id,
        "scope": "self",
        "metrics_available_at": "/employee/analytics/performance",
    }


@router.get("/performance")
def get_my_performance(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(require_feature("analytics.read")),
    period: str = Query("30d", pattern="^(7d|30d|90d)$"),
):
    user_id = _current_user_id(current_user)
    return {
        "user_id": user_id,
        "period": period,
        "performance": {},
    }


@router.get("/team")
def get_team_analytics(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(require_feature("analytics.reports.read")),
    period: str = Query("30d", pattern="^(7d|30d|90d)$"),
):
    return {
        "scope": "team",
        "period": period,
        "team_metrics": {},
    }


@router.get("/okr")
def get_okr_progress(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(require_feature("analytics.read")),
):
    user_id = _current_user_id(current_user)
    return {
        "user_id": user_id,
        "okrs": [],
    }


@router.get("/provider/summary")
def get_provider_summary(
    current_user: dict = Depends(get_current_user),
    _: None = Depends(require_feature("analytics.dashboard.view")),
    country_code: str | None = Query(None),
    period: str = Query("30d"),
):
    return _get_analytics_summary_provider(country_code=country_code, period=period)
