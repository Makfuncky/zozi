"""Customer customers router — consolidated from 3 source files."""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status


router = APIRouter(prefix="/api/v1/customer/customers", tags=["customer", "customers"])


# === From customer_health.py ===
"""
Customer Health API Endpoints
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from rbac import get_current_user
from infrastructure.database.database import get_db
from domains.customers.services.customer_health_engine import get_customer_health_engine

@router.get("/health/customers/{user_id}")
def get_customer_health(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    engine = get_customer_health_engine(db)
    return engine.calculate_health_score(user_id)


@router.get("/health/customers")
def list_customer_health(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    page: int = 1,
    size: int = 100,
):
    from domains.governance.models.user import User
    from infrastructure.utils.pagination import paginated_query

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



# === From customer_health_list.py ===
"""
Customer Health API Endpoints
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from infrastructure.database.database import get_db
from rbac import get_current_user
from domains.customers.services.customer_health_engine import get_customer_health_engine

@router.get("/health/customers/{user_id}")
def get_customer_health(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    engine = get_customer_health_engine(db)
    return engine.calculate_health_score(user_id)


@router.get("/health/customers")
def list_customer_health(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    page: int = 1,
    size: int = 100,
):
    from infrastructure.utils.pagination import paginated_query
    from domains.governance.models.user import User

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



# === From health.py ===
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

