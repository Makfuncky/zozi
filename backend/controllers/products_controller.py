"""Backward-compatible re-exports from the catalog domain.

All product-related CRUD logic lives in controllers.catalog.products_controller.
"""
from controllers.catalog.products_controller import (
    get_products,
    get_product,
    get_product_by_barcode,
    get_supplier_names,
    get_recommended_products,
    autocomplete_products,
)  # noqa: F401

# Imported from product_utils for convenience
from data.catalog_product_utils import _bump_product_cache_version  # noqa: F401

__all__ = [
    "get_products",
    "get_product",
    "get_product_by_barcode",
    "get_supplier_names",
    "get_recommended_products",
    "autocomplete_products",
    "_bump_product_cache_version",
]
