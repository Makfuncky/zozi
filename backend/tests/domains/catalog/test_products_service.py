"""Catalog domain — products service smoke test.

Verifies that ``domains.catalog.services.products.products_service.get_products``
returns a list and total count from the database. This is a basic smoke test
ensuring the products service can be called and returns a valid response.

Per ARCHITECTURE_DIAGRAM.md Law 69 (domain smoke tests).
"""
from __future__ import annotations

import pytest


@pytest.mark.smoke
@pytest.mark.catalog
def test_get_products_returns_paginated_list() -> None:
    """get_products should return a tuple of (items, total)."""
    from domains.catalog.services.products.products_service import get_products
    from infrastructure.database.database import get_db

    db = next(get_db())
    try:
        products, total = get_products(db, None, limit=5, offset=0)
        assert isinstance(products, list), "products must be a list"
        assert isinstance(total, int), "total must be an int"
        assert total >= 0, "total must be non-negative"
        if products:
            assert len(products) <= 5, "limit must be respected"
            for p in products[:3]:
                assert hasattr(p, "name"), "product must have a name attribute"
    finally:
        db.close()
