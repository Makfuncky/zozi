"""Service methods for country cross-border analytics."""
from __future__ import annotations
from sqlalchemy.orm import Session
from typing import Any
import logging
logger = logging.getLogger(__name__)



def get_customer_cross_border_stats(db: Session, customer_id: int, limit: int = 20, cursor: str | None = None) -> dict[str, Any]:
    """Return cross-border spending stats for a customer (cursor-paginated)."""
    from data.models import Order, User


    user = db.query(User).filter(User.id == customer_id).first()
    if not user:
        return {"user": None, "current_country": "AE", "orders": [], "next_cursor": None}

    current_country = user.country_code or "AE"
    query = (
        db.query(Order.id, Order.currency, Order.shipping_country)
        .filter(Order.customer_id == customer_id)
        .filter(Order.shipping_country != None)
        .order_by(Order.id.asc())
    )
    if cursor:
        try:
            query = query.filter(Order.id > int(cursor))
        except (TypeError, ValueError):
            pass
            logger.exception("Handled Exception")
    rows = query.limit(limit).all()
    orders = [(r.currency, r.shipping_country) for r in rows]
    next_cursor = str(rows[-1].id) if rows else None
    return {
        "user": user,
        "current_country": current_country,
        "orders": orders,
        "next_cursor": next_cursor,
    }
