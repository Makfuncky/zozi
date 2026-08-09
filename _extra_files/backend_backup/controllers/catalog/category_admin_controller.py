from __future__ import annotations
"""Admin category management controller.

Re-exports the catalog category-service operations so routers depend on the
controller boundary instead of reaching directly into ``services.catalog``.
"""

from services.catalog.category_service import (
    get_category_query,
    get_category_by_ref,
    get_category_by_id,
    category_slug_exists,
    create_category,
    update_category,
    deactivate_category,
)

__all__ = [
    "get_category_query",
    "get_category_by_ref",
    "get_category_by_id",
    "category_slug_exists",
    "create_category",
    "update_category",
    "deactivate_category",
]
