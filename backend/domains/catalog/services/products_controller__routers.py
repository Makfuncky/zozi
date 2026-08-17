"""Product controller.

Thin controller layer that exposes product business logic backed by
``services.products.products_service``. Routers delegate product operations to
this module via the import path ``controllers.products.products_controller``.
"""
from domains.catalog.services import products_service as _products_service

# Re-export the public service API so this controller mirrors it (the hollow
# product routers enumerate dir() to report available functions).
for _name, _obj in vars(_products_service).items():
    if _name.startswith("_") or not callable(_obj):
        continue
    globals()[_name] = _obj

# Explicitly expose the private cache-bump helper used by admin_catalog_operations.
from domains.catalog.services.products_service import _bump_product_cache_version  # noqa: E402,F401

# --- auto-wiring re-exports (added by fix_modules) ---
from domains.catalog.services.products_service import get_products
