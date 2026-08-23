"""Customer health service — orchestrates health-score reads for authenticated users."""
from __future__ import annotations

from sqlalchemy.orm import Session

from domains.customers.services.customer_health_engine import get_customer_health_engine
from infrastructure.utils.pagination import paginated_query


def get_customer_health(user_id: int, current_user: dict, db: Session):
    engine = get_customer_health_engine(db)
    return engine.calculate_health_score(user_id)


def list_customer_health(current_user: dict, db: Session, page: int, size: int):
    from domains.accounts.models.user import User

    users, total = paginated_query(
        db.query(User).order_by(User.created_at.desc()),
        page=page,
        size=min(size, 100),
        max_size=100,
    )
    results = []
    for u in users:
        engine = get_customer_health_engine(db)
        health = engine.calculate_health_score(u.id)
        health["profile"] = {
            "email": u.email,
            "role": u.role,
        }
        results.append(health)
    results.sort(key=lambda x: x.get("trust_score", 0), reverse=True)
    return {"customers": results, "total": total, "page": page, "size": size}
