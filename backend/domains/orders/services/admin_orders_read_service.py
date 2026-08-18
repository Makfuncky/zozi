"""Read helpers for admin order listing.

Extracted from ``routers/admin_orders_status.py`` so the router stays a thin
HTTP layer (W1: routers must not issue DB queries directly). The router sets
the country RLS context; this service only builds and runs the query.
"""
from __future__ import annotations

import math

from sqlalchemy.orm import Session

from domains.orders.models.orders import Order


def list_orders_paginated(
    db: Session,
    *,
    page: int,
    size: int,
    status: str | None = None,
    include_deleted: bool = False,
) -> dict:
    """Paginated admin order list (country scoping applied via RLS in the router)."""
    q = db.query(Order)
    if status:
        q = q.filter(Order.status == status)
    if not include_deleted:
        q = q.filter(Order.is_deleted == False)
    total = q.count()
    items = q.order_by(Order.created_at.desc()).offset((page - 1) * size).limit(size).all()
    return {
        "items": items,
        "total": total,
        "page": page,
        "pages": math.ceil(total / size) if total else 1,
    }
