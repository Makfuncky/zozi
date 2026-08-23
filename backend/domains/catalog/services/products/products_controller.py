"""Product service public API.

Backward-compatible re-export surface for product business logic. Module
routers import service functions through this path. New code should import
directly from `domains.catalog.services.products.products_service`.
"""
from __future__ import annotations

from domains.catalog.services.products.products_service import _bump_product_cache_version  # noqa: F401
from domains.catalog.services.products.products_service import get_product  # noqa: F401
from domains.catalog.services.products.products_service import get_product_by_barcode  # noqa: F401
from domains.catalog.services.products.products_service import get_products  # noqa: F401
from domains.catalog.services.products.products_service import get_supplier_names  # noqa: F401
from domains.catalog.services.products.admin_products_service import approve_product_route  # noqa: F401
from domains.catalog.services.products.admin_products_service import bulk_delete_products_route  # noqa: F401
from domains.catalog.services.products.admin_products_service import list_pending_products  # noqa: F401
from domains.catalog.services.products.admin_products_service import reject_product_route  # noqa: F401
from domains.catalog.services.products.admin_products_service import toggle_product_badge_route  # noqa: F401
from domains.catalog.services.products.admin_products_service import unarchive_product_route  # noqa: F401