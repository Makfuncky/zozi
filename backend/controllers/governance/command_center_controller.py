"""controllers.governance.command_center_controller controller.

Business logic is delegated to services.governance.command_center_service (routers -> controllers -> services)."""

from services.governance.command_center_service import (
    AlertResponse, CommandCenterDashboardResponse, ConnectionManager, FraudAlertResponse, NewsArticleResponse, RealtimeMetrics,
    SystemMetricsResponse, TreasuryMetricsResponse, _ALLOWED_TABLES, _validate_table_name, active_connections, create_executive_news,
    delete_executive_news, get_alerts, get_command_center, get_command_center_headlines, get_comprehensive_dashboard, get_dashboard,
    get_dashboard_stats, get_executive_news, get_fraud_alerts, get_realtime_metrics, get_system_metrics, get_treasury_metrics,
    manager, resolve_alert, router, safe_count, safe_fetch, safe_scalar,
    websocket_endpoint
)

__all__ = [
    "AlertResponse", "CommandCenterDashboardResponse", "ConnectionManager", "FraudAlertResponse", "NewsArticleResponse", "RealtimeMetrics",
    "SystemMetricsResponse", "TreasuryMetricsResponse", "_ALLOWED_TABLES", "_validate_table_name", "active_connections", "create_executive_news",
    "delete_executive_news", "get_alerts", "get_command_center", "get_command_center_headlines", "get_comprehensive_dashboard", "get_dashboard",
    "get_dashboard_stats", "get_executive_news", "get_fraud_alerts", "get_realtime_metrics", "get_system_metrics", "get_treasury_metrics",
    "manager", "resolve_alert", "router", "safe_count", "safe_fetch", "safe_scalar",
    "websocket_endpoint"
]
