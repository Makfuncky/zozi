"""Analytics controller for security domain.

Re-exports from admin.analytics for backward compatibility.
"""
from controllers.analytics.admin_analytics_controller import *  # noqa: F401, F403

__all__ = [
    "get_analytics",
    "get_analytics_timeseries",
    "get_top_products_analytics",
    "get_user_growth_analytics",
    "get_chatbot_analytics",
    "ROLE_PERMISSION_MAP",
    "VALID_USER_ROLES",
]