"""controllers.admin.database controller.

Business logic is delegated to services.admin.database_service (routers -> controllers -> services)."""

from services.admin.database_service import (
    _database_architecture_snapshot, _database_health_snapshot, _postgres_service_snapshot, _redis_service_snapshot, _safe_database_location, _sqlite_service_snapshot,
    _table_column_details, _table_row_count, get_database_overview
)

__all__ = [
    "_database_architecture_snapshot", "_database_health_snapshot", "_postgres_service_snapshot", "_redis_service_snapshot", "_safe_database_location", "_sqlite_service_snapshot",
    "_table_column_details", "_table_row_count", "get_database_overview"
]
