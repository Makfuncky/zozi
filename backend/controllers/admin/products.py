"""Admin product management controller.

Backward-compatible re-exports for importers that reference the old
controllers.admin.products path.  Canonical module lives in
controllers/catalog/products.py.
"""
from controllers.catalog.products import (  # noqa: F401
    get_all_products,
    delete_product_admin,
    restore_product_admin,
    get_pending_products,
    approve_product,
    reject_product,
    toggle_product_badge,
    bulk_delete_products_admin,
    bulk_product_moderation,
)
