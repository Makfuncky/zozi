"""Customer Health API endpoints (routers layer, single source of truth).

Thin HTTP layer: delegates all scoring to
``domains.customers.services.customer_health_engine``. Consolidates the previously
duplicated ``customer_health.py`` (prefix-less) and ``customer_health_list.py``
(``/api/v1``) routers under the actor-namespaced ``/api/v1/customer/health``
prefix (RESOLVER §27 CD3, fixes CUST-D2/D3).
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from infrastructure.utils.dependencies import get_current_user
from rbac.dependencies import require_feature
from infrastructure.database.database import get_db
from domains.customers.services.customer_health_engine import get_customer_health_engine
from domains.customers.services.customer_health_engine import list_customer_health as svc_list_customer_health

router = APIRouter(prefix="/api/v1/customer/health")


@router.get("/customers/{user_id}")
def get_customer_health(
    user_id: int,
    _: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    _gate: None = Depends(require_feature("customers.customer.read")),
):
    engine = get_customer_health_engine(db)
    return engine.calculate_health_score(user_id)


@router.get("/customers")
def list_customer_health(
    _: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    size: int = Query(100, ge=1, le=100),
):
    return svc_list_customer_health(db, page=page, size=size)
