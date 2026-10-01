"""Customer health service — orchestrates health-score reads for authenticated users."""
from __future__ import annotations

from datetime import timedelta

from sqlalchemy.orm import Session

from domains.customers.services.customer_health_engine import (
    calculate_health_score_from_data,
    get_customer_health_engine,
)
from infrastructure.utils.datetime_utils import utcnow
from infrastructure.utils.pagination import paginated_query


def get_customer_health(user_id: int, current_user: dict, db: Session):
    engine = get_customer_health_engine(db)
    return engine.calculate_health_score(user_id)


def list_customer_health(current_user: dict, db: Session, page: int, size: int):
    from domains.accounts.models.user import User
    from domains.orders.models.orders import Order, ReturnRequest

    page = max(1, page)
    size = min(max(1, size), 100)
    users, total = paginated_query(
        db.query(User).order_by(User.created_at.desc()),
        page=page,
        size=size,
        max_size=100,
    )
    if not users:
        return {"customers": [], "total": total, "page": page, "size": size, "pages": 0}

    user_ids = [u.id for u in users]
    now = utcnow()
    thirty_days_ago = now - timedelta(days=30)

    all_orders = (
        db.query(Order)
        .filter(
            Order.user_id.in_(user_ids),
            Order.created_at >= thirty_days_ago,
            Order.created_at <= now,
        )
        .all()
    )
    orders_by_user: dict[int, list] = {}
    for o in all_orders:
        orders_by_user.setdefault(o.user_id, []).append(o)

    all_order_ids = [o.id for o in all_orders]
    all_returns: list = []
    if all_order_ids:
        all_returns = (
            db.query(ReturnRequest)
            .filter(ReturnRequest.order_id.in_(all_order_ids))
            .all()
        )
    returns_by_order: dict[int, list] = {}
    for r in all_returns:
        returns_by_order.setdefault(r.order_id, []).append(r)

    results = []
    for u in users:
        orders = orders_by_user.get(u.id, [])
        returns = [r for o in orders for r in returns_by_order.get(o.id, [])]
        health = calculate_health_score_from_data(db, u, orders, returns)
        health["profile"] = {
            "email": u.email,
            "role": u.role,
        }
        results.append(health)
    results.sort(key=lambda x: x.get("trust_score", 0), reverse=True)
    return {
        "customers": results,
        "total": total,
        "page": page,
        "size": size,
        "pages": max(1, (total + size - 1) // size),
    }
