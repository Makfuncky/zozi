"""Auto-migrated service logic from routers/customer_health_list.py."""
from __future__ import annotations

from fastapi import Depends

from sqlalchemy.orm import Session

from infrastructure.database.database import get_db

from domains.governance.services.auth_controller_service import get_current_user

from domains.customers.services.customer_health_engine import get_customer_health_engine


def list_customer_health(current_user: dict, db: Session, page: int, size: int):
    from infrastructure.utils.pagination import paginated_query
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









