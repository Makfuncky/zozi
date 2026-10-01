"""Supplier customers router — read-only customer reviews on supplier products.

Thin HTTP surface (ARCHITECTURE_DIAGRAM.md §3). Suppliers see review signal
on their own catalogue (used for moderation / quality). No customer PII
exposed; only public review content.
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from domains.customers.services.reviews_service import get_product_reviews
from infrastructure.database.database import get_db
from rbac import get_current_user
from rbac.dependencies import require_feature

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/supplier/customers", tags=["supplier", "customers"])


@router.get("/reviews/products/{product_id}")
def list_product_reviews(
    product_id: int,
    limit: int = Query(50, ge=1, le=200),
    cursor: Optional[int] = Query(None),
    current_user: dict = Depends(get_current_user),
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
