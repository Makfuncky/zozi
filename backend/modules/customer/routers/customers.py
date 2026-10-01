from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status
from sqlalchemy.orm import Session
from rbac import get_current_user
from rbac.dependencies import require_feature
from infrastructure.database.database import get_db
from domains.customers.services.customer_health_engine import get_customer_health_engine
from domains.customers.services.customer_health_engine import list_customer_health as svc_list_customer_health


"""Customer customers router — consolidated from 3 source files."""




router = APIRouter(prefix="/api/v1/customer/customers", tags=["customer", "customers"])


# === From customer_health.py ===
"""
Customer Health API Endpoints
"""


@router.get("/health/customers/{user_id}")
def get_customer_health(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("customers.health.view")),
):
    engine = get_customer_health_engine(db)
    return engine.calculate_health_score(user_id)


@router.get("/health/customers")
def list_customer_health(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    page: int = 1,
    size: int = 100,
    _rf_gate: None = Depends(require_feature("customers.health.view")),
):
    return svc_list_customer_health(db, page=page, size=size)
