"""Employee customers router — read-only operational view of customers.

Thin HTTP surface (ARCHITECTURE_DIAGRAM.md §3). Employees are not allowed to
edit customer data; this router only exposes operational views needed for
support and triage (health, reviews on products, top-N health list).
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from domains.customers.services.customer_health_engine import (
    get_customer_health_engine,
    list_customer_health as svc_list_customer_health,
)
from domains.customers.services.reviews_service import get_product_reviews
from infrastructure.database.database import get_db
from rbac import get_current_user
from rbac.dependencies import require_feature

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/employee/customers", tags=["employee", "customers"])


@router.get("/health/customers")
def list_customer_health(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    size: int = Query(100, ge=1, le=100),
    _gate: None = Depends(require_feature("customers.health.view")),
):
    try:
        return svc_list_customer_health(db, page=page, size=size)
    except Exception as exc:
        logger.error("Error listing customer health: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/health/customers/{user_id}")
def get_customer_health(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    _gate: None = Depends(require_feature("customers.health.view")),
):
    try:
        engine = get_customer_health_engine(db)
        return engine.calculate_health_score(user_id)
    except Exception as exc:
        logger.error("Error computing health for customer %s: %s", user_id, exc)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/reviews/products/{product_id}")
def list_product_reviews(
    product_id: int,
    limit: int = Query(50, ge=1, le=200),
    cursor: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    _gate: None = Depends(require_feature("customers.reviews.write")),
):
    try:
        return get_product_reviews(
            db=db, product_id=product_id, limit=limit, cursor=cursor
        )
    except Exception as exc:
        logger.error("Error listing product reviews: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error")
