"""Customer health list service — delegates to customer_health_engine."""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from domains.customers.services.customer_health_engine import get_customer_health_engine

logger = logging.getLogger(__name__)


def list_customer_health_metrics(user_id: int, country_code: Optional[str], db: Session, current_user: dict):
    """List customer health metrics visible to the requesting user."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    engine = get_customer_health_engine(db)
    return {"metrics": [engine.calculate_health_score(user_id)], "country_code": country_code}


def get_customer_health_detail(customer_id: int, db: Session, current_user: dict):
    """Fetch health detail for a single customer."""
    engine = get_customer_health_engine(db)
    return engine.calculate_health_score(customer_id)
