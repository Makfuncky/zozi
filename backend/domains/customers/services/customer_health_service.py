"""Auto-migrated service logic from routers/customer_health.py."""
from __future__ import annotations

from sqlalchemy.orm import Session

from domains.customers.services.customer_health_engine import get_customer_health_engine
from domains.customers.services.customer_health_engine import list_customer_health as _list_customer_health


def get_customer_health(user_id: int, current_user: dict, db: Session):
    engine = get_customer_health_engine(db)
    return engine.calculate_health_score(user_id)


def list_customer_health(current_user: dict, db: Session, page: int, size: int):
    return _list_customer_health(db=db, page=page, size=size)


