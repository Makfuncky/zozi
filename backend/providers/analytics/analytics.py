"""
Analytics Provider
==================
AI analysis for Admin analytics.
Test file: backend/tests/_test_provider/test_analytics.py
"""
from __future__ import annotations
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


class settings:
    analytics_timeout = 30
    dashboard_model = "gpt-4o-mini"
    report_model = "gpt-4o-mini"
    kpi_model = "gpt-4o-mini"

logger = logging.getLogger(__name__)


class AnalyticsProvider:
    """AI analysis for admin analytics."""

    def __init__(self):
        self._default_period_days = settings.analytics_default_period_days

    def get_dashboard_summary(
        self,
        country_code: Optional[str] = None,
        period: str = "30d",
    ) -> Dict[str, Any]:
        """Get dashboard summary metrics.

        Args:
            country_code: Optional ISO country code for filtering.
            period: Time period (7d, 30d, 90d, 1y).

        Returns:
            Dict with dashboard metrics.
        """
        days_map = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}
        days = days_map.get(period, self._default_period_days)
        since = datetime.utcnow() - timedelta(days=days)

        return {
            "period": period,
            "days": days,
            "since": since.isoformat(),
            "country_code": country_code,
            "total_users": 0,
            "total_suppliers": 0,
            "total_products": 0,
            "total_orders": 0,
            "total_revenue": 0.0,
            "message": "Connect to a database for live analytics data.",
        }

    def get_chatbot_analytics(
        self,
        country_code: Optional[str] = None,
        period: str = "30d",
    ) -> Dict[str, Any]:
        """Get chatbot analytics data.

        Args:
            country_code: Optional ISO country code for filtering.
            period: Time period (7d, 30d, 90d, 1y).

        Returns:
            Dict with chatbot analytics.
        """
        days_map = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}
        days = days_map.get(period, self._default_period_days)

        return {
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
            "message": "Connect to a database for live chatbot analytics.",
        }

    def get_product_performance(
        self,
        country_code: Optional[str] = None,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """Get product performance analytics.

        Args:
            country_code: Optional ISO country code for filtering.
            limit: Maximum number of products to return.

        Returns:
            Dict with product performance data.
        """
        return {
            "country_code": country_code,
            "limit": limit,
            "top_products": [],
            "message": "Connect to a database for live product performance data.",
        }

    def get_sales_trends(
        self,
        country_code: Optional[str] = None,
        period: str = "30d",
    ) -> Dict[str, Any]:
        """Get sales trend data.

        Args:
            country_code: Optional ISO country code for filtering.
            period: Time period (7d, 30d, 90d, 1y).

        Returns:
            Dict with sales trend data.
        """
        days_map = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}
        days = days_map.get(period, self._default_period_days)

        return {
            "period": period,
            "days": days,
            "country_code": country_code,
            "trends": [],
            "message": "Connect to a database for live sales trend data.",
        }

    def get_ai_insights(
        self,
        country_code: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get AI-generated insights for admin dashboard.

        Args:
            country_code: Optional ISO country code for filtering.

        Returns:
            Dict with AI insights.
        """
        return {
            "country_code": country_code,
            "insights": [],
            "recommendations": [],
            "message": "AI insights require database connectivity.",
        }