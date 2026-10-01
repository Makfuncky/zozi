"""Catalog domain — feature flags (Law 4).

Feature atoms are single-sourced here and aggregated by ``rbac/catalog.py``.
"""

FEATURES = {
    "catalog.product.create": "Create and publish products",
    "catalog.category.manage": "Manage product categories",
    "catalog.search.advanced": "Advanced catalog search and filtering",
    "catalog.list": "List and browse catalog products",
    "catalog.read": "View catalog product details",
    "catalog.write": "Create and update catalog products",
    "catalog.delete": "Delete catalog products",
}

__all__ = ["FEATURES"]
