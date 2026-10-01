"""Orders router for logistics module — thin delegating to domain services."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from infrastructure.database.database import get_db
from infrastructure.security.dependencies import require_logistics
from rbac.dependencies import require_feature
from domains.orders.ports import get_available_orders_for_logistics
from domains.orders.services.logistics_service import get_orders_to_fulfil

router = APIRouter(prefix="/api/v1/logistics/orders", tags=["logistics", "orders"])


@router.get("")
def list_orders_to_fulfil(
    current_user: dict = Depends(require_logistics),
    db: Session = Depends(get_db),
    limit: int = Query(200, ge=1, le=200),
    offset: int = Query(0, ge=0),
    _rf_gate: None = Depends(require_feature("logistics.fulfillment.manage")),
):
    """List orders awaiting fulfilment."""
    return get_orders_to_fulfil(current_user, db, limit=limit, offset=offset)


@router.get("/available")
def list_available_orders(
    current_user: dict = Depends(require_logistics),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("logistics.fulfillment.manage")),
):
    """List all orders in 'prepared' status available for pickup."""
    return get_available_orders_for_logistics(db)
