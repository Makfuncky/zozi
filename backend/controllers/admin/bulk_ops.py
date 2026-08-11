"""controllers.admin.bulk_ops controller.

Business logic is delegated to services.admin.bulk_ops_service (routers -> controllers -> services)."""

from services.admin.bulk_ops_service import (
    bulk_archive_entities, bulk_category_change, bulk_restore_entities
)

__all__ = [
    "bulk_archive_entities", "bulk_category_change", "bulk_restore_entities"
]
