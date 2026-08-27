"""Read helpers for admin category listing.

Extracted from ``routers/admin_catalog_orders.py`` so the router stays a thin
HTTP layer (W1: routers must not issue DB queries directly).
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from domains.catalog.models.products import Category


def list_categories_paginated(
    db: Session,
    *,
    country_code: str,
    include_deleted: bool,
    page: int,
    page_size: int,
) -> dict:
    """Country-scoped, paginated category list used by the admin category grid."""
    q = db.query(Category).filter(Category.country_code == country_code)
    if not include_deleted:
        q = q.filter(Category.is_active == True)
    total = q.count()
    # NOTE: OFFSET pagination is acceptable here because:
    # 1. Category lists are typically small (<100 rows) and bounded
    # 2. Admin UIs rarely page beyond the first few results
    # 3. sort_order index makes the ORDER BY + OFFSET efficient for small tables
    rows = q.order_by(Category.sort_order).offset((page - 1) * page_size).limit(page_size).all()
    return {"data": rows, "total": total, "page": page, "page_size": page_size}
