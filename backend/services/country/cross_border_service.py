"""Service methods for country cross-border analytics."""
from __future__ import annotations
from sqlalchemy.orm import Session
from typing import Any


def get_customer_cross_border_stats(db: Session, customer_id: int, skip: int = 0, limit: int = 20) -> dict[str, Any]:
    """Return cross-border spending stats for a customer."""
    from data.models import Order, User

    user = db.query(User).filter(User.id == customer_id).first()
    if not user:
        return {"user": None, "current_country": "AE", "orders": []}

    current_country = user.country_code or "AE"
    orders = (
        db.query(Order.currency, Order.shipping_country)
        .filter(Order.customer_id == customer_id)
        .filter(Order.shipping_country != None)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return {
        "user": user,
        "current_country": current_country,
        "orders": orders,
    }
