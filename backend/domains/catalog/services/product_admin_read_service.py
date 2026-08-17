"""Read helpers for admin product catalogue listing.

Extracted from ``routers/admin_catalog_operations.py`` so the router stays a
thin HTTP layer (W1: routers must not issue DB queries directly).
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from _legacy.models import Product
from utils.pagination import paginated_response


def list_products_paginated(
    db: Session,
    *,
    country_code: str,
    page: int,
    size: int,
    moderation_status: str | None = None,
    include_deleted: bool = False,
) -> dict:
    """Country-scoped, paginated product list used by the admin catalogue grid."""
    q = db.query(Product).filter(Product.country_code == country_code)
    if moderation_status:
        q = q.filter(Product.moderation_status == moderation_status)
    if not include_deleted:
        q = q.filter(Product.is_deleted == False)
    return paginated_response(q, page, size)
