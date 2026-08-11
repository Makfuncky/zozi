"""controllers.analytics.analytics controller.

Business logic is delegated to services.analytics.analytics_service (routers -> controllers -> services)."""

from services.analytics.analytics_service import (
    ROLE_PERMISSION_MAP, _ANALYTICS_CACHE_TTL_SECONDS, _PERIOD_DAYS, _get_admin_analytics_payload, _load_admin_analytics_snapshot, _safe_load_chatbot_filters,
    get_analytics, get_analytics_timeseries, get_chatbot_analytics, get_customer_insights, get_top_products_analytics, get_user_growth_analytics,
    logger
)

__all__ = [
    "ROLE_PERMISSION_MAP", "_ANALYTICS_CACHE_TTL_SECONDS", "_PERIOD_DAYS", "_get_admin_analytics_payload", "_load_admin_analytics_snapshot", "_safe_load_chatbot_filters",
    "get_analytics", "get_analytics_timeseries", "get_chatbot_analytics", "get_customer_insights", "get_top_products_analytics", "get_user_growth_analytics",
    "logger"
]
