"""Logistics customers router — minimal customer surface for delivery ops.

Thin HTTP surface (ARCHITECTURE_DIAGRAM.md §3). Logistics partners need only
the address/contact data needed to fulfil a delivery, exposed through the
sanctioned ``customers.ports`` readers. No PII beyond the delivery envelope.
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from domains.customers.ports import list_user_addresses
from infrastructure.database.database import get_db
from rbac import get_current_user
from rbac.dependencies import require_feature

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/logistics/customers", tags=["logistics", "customers"])


@router.get("/addresses/{user_id}")
def get_customer_delivery_addresses(
    user_id: int,
    limit: int = Query(20, ge=1, le=100),
    cursor: Optional[int] = Query(None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    _gate: None = Depends(require_feature("customers.address.manage")),
):
    try:
        rows = list_user_addresses(db, user_id, limit=limit, cursor=cursor)
        return [
            {
                "id": getattr(row, "id", None),
                "label": getattr(row, "label", None),
                "address_line1": getattr(row, "address_line1", None),
                "address_line2": getattr(row, "address_line2", None),
                "city": getattr(row, "city", None),
                "state": getattr(row, "state", None),
                "postal_code": getattr(row, "postal_code", None),
                "country": getattr(row, "country", None),
                "phone": getattr(row, "phone", None),
                "is_default": getattr(row, "is_default", False),
            }
            for row in rows
        ]
    except Exception as exc:
        logger.error("Error fetching delivery addresses for %s: %s", user_id, exc)
        raise HTTPException(status_code=500, detail="Internal server error")
