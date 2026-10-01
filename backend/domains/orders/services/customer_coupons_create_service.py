"""Customer coupon lifecycle controller (orders domain).

Thin facade used by the (archived) promotions coupon service. Coupon storage
lives in governance; this module provides the `delete_coupon` symbol the
promotions package expects, delegating to the governance coupons surface.
Degrades gracefully (Law 30) if the backing coupon record is unavailable.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

# LAZY: from domains.governance.ports import list_coupons

logger = logging.getLogger(__name__)


def delete_coupon(db: Any, coupon_id: int, current_user: Optional[dict] = None) -> dict:
    """Delete (deactivate) a customer coupon.

    The canonical coupon model is owned by governance; we resolve the coupon by
    id via the governance ports surface and mark it inactive when present.
    Returns a status dict so callers never need to distinguish ownership.
    """
    try:
        coupons = list_coupons(db, limit=10000) or []
        target = next((c for c in coupons if getattr(c, "id", None) == coupon_id), None)
        if target is None:
            return {"id": coupon_id, "deleted": False, "note": "coupon not found"}
        if hasattr(target, "is_active"):
            target.is_active = False
            db.flush()
        return {"id": coupon_id, "deleted": True}
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("delete_coupon failed: %s", exc)
        return {"id": coupon_id, "deleted": False, "error": str(exc)}
