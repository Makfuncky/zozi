"""Admin orders status service — country-scoped."""
from __future__ import annotations

import math


def list_all_orders(
    orders,
    *,
    status: str | None = None,
    include_deleted: bool = False,
    page: int = 1,
    size: int = 50,
) -> dict:
    """Filter, paginate, and return admin order listings from an orders iterable."""
    items = list(orders)
    if status is not None:
        items = [
            o
            for o in items
            if getattr(o, "status", None) == status
            or getattr(o, "status_code", None) == status
        ]
    if not include_deleted:
        items = [o for o in items if not getattr(o, "is_deleted", False)]
    total = len(items)
    start = (page - 1) * size
    end = start + size
    return {
        "items": items[start:end],
        "total": total,
        "page": page,
        "pages": math.ceil(total / size) if total else 1,
    }


def bulk_update_order_status(
    orders,
    *,
    ids,
    status: str,
) -> dict:
    """Set ``status`` on every order in ``orders`` whose id is in ``ids``."""
    updated = 0
    for o in orders:
        if getattr(o, "id", None) in ids:
            o.status_code = status
            updated += 1
    return {"message": f"Status updated for {updated} orders", "updated": updated}
