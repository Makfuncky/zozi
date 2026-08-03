"""Admin analytics router."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from data.db import get_db
from utils.dependencies import require_admin
from controllers.analytics.admin_analytics_controller import (
    get_analytics,
    get_analytics_timeseries,
    get_top_products_analytics,
    get_user_growth_analytics,
    get_customer_insights,
    refresh_admin_analytics_snapshots,
)

router = APIRouter()


@router.get("/admin/analytics")
def get_analytics_endpoint(
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
):
    return get_analytics(db)


@router.get("/admin/analytics/timeseries")
def get_timeseries(
    period: str = "30d",
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
):
    return get_analytics_timeseries(period, db)


@router.get("/admin/analytics/top-products")
def get_top_products(
    limit: int = 10,
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
):
    return get_top_products_analytics(limit, db)


@router.get("/admin/analytics/user-growth")
def get_user_growth(
    period: str = "30d",
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
):
    return get_user_growth_analytics(period, db)


@router.get("/admin/analytics/customer-insights")
def get_customer_insights(
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
):
    return get_customer_insights(db)