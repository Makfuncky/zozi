"""controllers.admin.analytics controller.

Business logic is delegated to services.admin.analytics_service (routers -> controllers -> services)."""

from services.admin.analytics_service import (
    ROLE_PERMISSION_MAP, VALID_USER_ROLES, _ALLOWED_BANK_ACCOUNT_KINDS, _ANALYTICS_CACHE_TTL_SECONDS, _ANALYTICS_SNAPSHOT_TTL, _PERIOD_DAYS,
    _compute_analytics_overview, _compute_analytics_timeseries_payload, _compute_top_products_payload, _compute_user_growth_payload, _get_admin_analytics_payload, _load_admin_analytics_snapshot,
    _store_admin_analytics_snapshot, get_analytics, get_analytics_timeseries, get_chatbot_analytics, get_customer_insights, get_top_products_analytics,
    get_user_growth_analytics, refresh_admin_analytics_snapshots
)

__all__ = [
    "ROLE_PERMISSION_MAP", "VALID_USER_ROLES", "_ALLOWED_BANK_ACCOUNT_KINDS", "_ANALYTICS_CACHE_TTL_SECONDS", "_ANALYTICS_SNAPSHOT_TTL", "_PERIOD_DAYS",
    "_compute_analytics_overview", "_compute_analytics_timeseries_payload", "_compute_top_products_payload", "_compute_user_growth_payload", "_get_admin_analytics_payload", "_load_admin_analytics_snapshot",
    "_store_admin_analytics_snapshot", "get_analytics", "get_analytics_timeseries", "get_chatbot_analytics", "get_customer_insights", "get_top_products_analytics",
    "get_user_growth_analytics", "refresh_admin_analytics_snapshots"
]
