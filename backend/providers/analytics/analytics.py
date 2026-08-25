from __future__ import annotations

"""
Analytics Provider
=================
AI analysis for Admin analytics.
Test file: backend/tests/_test_provider/test_analytics.py
"""
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..config import settings

logger = logging.getLogger(__name__)

HAS_ANALYTICS = bool(os.environ.get("ANALYTICS_API_KEY", ""))


class AnalyticsProvider:
    """AI analysis for admin analytics."""

    def __init__(self):
        self._default_period_days = settings.analytics_default_period_days

    def get_dashboard_summary(
        self,
        country_code: Optional[str] = None,
        period: str = "30d",
    ) -> Dict[str, Any]:
        """Get dashboard summary metrics."""
        days_map = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}
        days = days_map.get(period, self._default_period_days)
        since = datetime.utcnow() - timedelta(days=days)

        base_result = {
            "period": period,
            "days": days,
            "since": since.isoformat(),
            "country_code": country_code,
            "total_users": 0,
            "total_suppliers": 0,
            "total_products": 0,
            "total_orders": 0,
            "total_revenue": 0.0,
        }

        if not HAS_ANALYTICS:
            base_result["message"] = (
                "Analytics provider not configured. Set ANALYTICS_API_KEY env var."
            )
            return base_result

        base_result["message"] = "Connect to a database for live analytics data."
        return base_result

    def get_chatbot_analytics(
        self,
        country_code: Optional[str] = None,
        period: str = "30d",
    ) -> Dict[str, Any]:
        """Get chatbot analytics data."""
        days_map = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}
        days = days_map.get(period, self._default_period_days)

        base_result = {
            "period": period,
            "days": days,
            "country_code": country_code,
            "total_queries": 0,
            "total_clicks": 0,
            "product_search_queries": 0,
            "avg_results_per_query": 0,
            "click_through_rate": 0,
            "top_queries": [],
            "top_intents": [],
            "top_clicked_products": [],
            "daily_data": [],
        }

        if not HAS_ANALYTICS:
            base_result["message"] = (
                "Analytics provider not configured. Set ANALYTICS_API_KEY env var."
            )
            return base_result

        base_result["message"] = "Connect to a database for live chatbot analytics."
        return base_result

    def get_product_performance(
        self,
        country_code: Optional[str] = None,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """Get product performance analytics."""
        base_result = {
            "country_code": country_code,
            "limit": limit,
            "top_products": [],
        }

        if not HAS_ANALYTICS:
            base_result["message"] = (
                "Analytics provider not configured. Set ANALYTICS_API_KEY env var."
            )
            return base_result

        base_result["message"] = "Connect to a database for live product performance data."
        return base_result

    def get_sales_trends(
        self,
        country_code: Optional[str] = None,
        period: str = "30d",
    ) -> Dict[str, Any]:
        """Get sales trend data."""
        days_map = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}
        days = days_map.get(period, self._default_period_days)

        base_result = {
            "period": period,
            "days": days,
            "country_code": country_code,
            "trends": [],
        }

        if not HAS_ANALYTICS:
            base_result["message"] = (
                "Analytics provider not configured. Set ANALYTICS_API_KEY env var."
            )
            return base_result

        base_result["message"] = "Connect to a database for live sales trend data."
        return base_result

    def get_ai_insights(
        self,
        country_code: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get AI-generated insights for admin dashboard."""
        base_result = {
            "country_code": country_code,
            "insights": [],
            "recommendations": [],
        }

        if not HAS_ANALYTICS:
            base_result["message"] = (
                "Analytics provider not configured. Set ANALYTICS_API_KEY env var."
            )
            return base_result

        base_result["message"] = "AI insights require database connectivity."
        return base_result