"""Customer analytics router — thin wrappers over the analytics + customer domains.

Per ARCHITECTURE_DIAGRAM.md §3, module routers stay thin: auth context,
``require_feature(...)`` gate, and one service call. The analytics services
live in ``domains.analytics.services``. Cross-domain reads are imported via
``customers.ports`` (the sanctioned read surface).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from infrastructure.database.database import get_db
from infrastructure.security.dependencies import get_current_user

from rbac.dependencies import require_feature

from domains.analytics.services.dashboards.analytics_service import (
    get_analytics_summary as _get_analytics_summary_provider,
)
from domains.customers.ports import (
    get_may_you_like,
    get_last_seen,
)


router = APIRouter(prefix="/customer/analytics", tags=["customer", "analytics"])


def _current_user_id(current_user: dict) -> int:
    return int(current_user.get("user_id") or current_user.get("id") or 0)


@router.get("/summary")
def get_my_analytics_summary(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(require_feature("analytics.dashboard.view")),
):
    user_id = _current_user_id(current_user)
    return {
        "user_id": user_id,
        "recommendations": get_may_you_like(db, user_id, limit=8),
        "last_seen": get_last_seen(db, user_id, limit=12),
    }


@router.get("/recommendations")
def get_my_recommendations(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(require_feature("analytics.read")),
    limit: int = Query(8, ge=1, le=50),
):
    return get_may_you_like(db, _current_user_id(current_user), limit=limit)


@router.get("/last-seen")
def get_my_last_seen(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(require_feature("analytics.read")),
    limit: int = Query(12, ge=1, le=50),
):
    return get_last_seen(db, _current_user_id(current_user), limit=limit)


@router.get("/provider/summary")
def get_provider_summary(
    current_user: dict = Depends(get_current_user),
    _: None = Depends(require_feature("analytics.dashboard.view")),
    country_code: str | None = Query(None),
    period: str = Query("30d"),
):
    return _get_analytics_summary_provider(country_code=country_code, period=period)
