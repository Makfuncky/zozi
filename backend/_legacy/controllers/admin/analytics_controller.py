"""Admin analytics controller (CONTROLLERS layer).

Canonical coordinator for admin analytics dashboards. Delegates to
``services.admin.analytics_service`` (and ``services.analytics.analytics_service``).

HTTP contract declared with ``core.route_contract`` decorators.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from core.route_contract import get

from utils.country_rls import get_country_or_404
from utils.rls_interceptor import set_rls_context, clear_rls_context

from services.admin.analytics_service import (
    get_analytics,
    get_analytics_timeseries,
    get_chatbot_analytics,
    get_customer_insights,
    get_top_products_analytics,
    get_user_growth_analytics,
)


def _with_rls(country_code: str, db: Session):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)


@get(
    "/api/v1/admin/analytics/{country_code}",
    deps=["db", "admin"],
    tags=["admin-analytics"],
)
def analytics_overview(country_code: str, current_user=None, db: Session = None):
    _with_rls(country_code, db)
    try:
        return get_analytics(db)
    finally:
        clear_rls_context()


@get(
    "/api/v1/admin/analytics/{country_code}/timeseries",
    deps=["db", "admin"],
    query=["period"],
    tags=["admin-analytics"],
)
def analytics_timeseries(
    country_code: str,
    period: str = "30d",
    current_user=None,
    db: Session = None,
):
    _with_rls(country_code, db)
    try:
        return get_analytics_timeseries(period, db)
    finally:
        clear_rls_context()


@get(
    "/api/v1/admin/analytics/{country_code}/customers",
    deps=["db", "admin"],
    tags=["admin-analytics"],
)
def analytics_customers(country_code: str, current_user=None, db: Session = None):
    _with_rls(country_code, db)
    try:
        return get_customer_insights(db)
    finally:
        clear_rls_context()


@get(
    "/api/v1/admin/analytics/{country_code}/top-products",
    deps=["db", "admin"],
    query=["limit"],
    tags=["admin-analytics"],
)
def analytics_top_products(
    country_code: str,
    limit: int = 10,
    current_user=None,
    db: Session = None,
):
    _with_rls(country_code, db)
    try:
        return get_top_products_analytics(limit, db)
    finally:
        clear_rls_context()


@get(
    "/api/v1/admin/analytics/{country_code}/user-growth",
    deps=["db", "admin"],
    query=["period"],
    tags=["admin-analytics"],
)
def analytics_user_growth(
    country_code: str,
    period: str = "30d",
    current_user=None,
    db: Session = None,
):
    _with_rls(country_code, db)
    try:
        return get_user_growth_analytics(period, db)
    finally:
        clear_rls_context()


@get(
    "/api/v1/admin/analytics/{country_code}/chatbot",
    deps=["db", "admin"],
    query=["period"],
    tags=["admin-analytics"],
)
def analytics_chatbot(
    country_code: str,
    period: str = "30d",
    current_user=None,
    db: Session = None,
):
    _with_rls(country_code, db)
    try:
        return get_chatbot_analytics(period, db)
    finally:
        clear_rls_context()
