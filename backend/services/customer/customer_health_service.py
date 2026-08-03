"""Customer health router logic, extracted behind the service layer (clears LC1).

Each function owns its database session via ``data.db.get_db_context`` so the
router layer never injects or touches a SQLAlchemy session directly.
"""
from data.models import User
from services.customer_health_engine import get_customer_health_engine
from utils.pagination import paginated_query


def get_customer_health(user_id: int) -> dict:
    from data.db import get_db_context

    with get_db_context() as db:
        engine = get_customer_health_engine(db)
        return engine.calculate_health_score(user_id)


def list_customer_health(page: int = 1, size: int = 100) -> dict:
    from data.db import get_db_context

    with get_db_context() as db:
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
            health["profile"] = {"email": u.email, "role": u.role}
            results.append(health)
        results.sort(key=lambda x: x.get("trust_score", 0), reverse=True)
        return {"customers": results, "total": total, "page": page, "size": size}
