from __future__ import annotations

"""Admin orders router — canonical."""

from fastapi import APIRouter, Depends, Query, Path, Body, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from infrastructure.database.database import get_db
from infrastructure.security.dependencies import require_admin
from rbac.dependencies import require_feature
from domains.comms.ports import (
    create_campaign,
    delete_campaign,
    list_all_campaigns,
    list_campaigns,
)
from domains.country.utils.country_rls import get_country_or_404
from infrastructure.database.rls_interceptor import set_rls_context, clear_rls_context
router = APIRouter(prefix="/api/v1/admin/orders", tags=["admin", "orders"])


@router.get("/campaigns", status_code=200)
def list_all_campaigns_route(_: dict = Depends(require_admin), db: Session = Depends(get_db)):
    require_feature("orders.list")
    return list_all_campaigns(db)


@router.get("/metrics")
def admin_email_metrics(_: dict = Depends(require_admin), db: Session = Depends(get_db)):
    require_feature("orders.read")
    # TODO: implement via domains.comms.services.email_metrics_service when wired
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="email_metrics not yet wired to a domain service",
    )


@router.get("/campaigns/{country_code}")
def list_campaigns_route(
    country_code: str = Path(..., description="ISO country code"),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    require_feature("orders.list")
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return list_campaigns(db, country_code, page, page_size)
    finally:
        clear_rls_context()


@router.post("/campaigns/{country_code}", status_code=201)
def create_campaign_route(
    country_code: str = Path(..., description="ISO country code"),
    payload: dict = Body(...),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    require_feature("orders.create")
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return create_campaign(db, payload, country_code)
    finally:
        clear_rls_context()


@router.delete("/campaigns/{country_code}/{campaign_id}")
def delete_campaign_route(
    country_code: str = Path(..., description="ISO country code"),
    campaign_id: int = Path(...),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    require_feature("orders.manage")
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return delete_campaign(db, campaign_id, country_code)
    finally:
        clear_rls_context()


@router.get("/admin_orders_routes/health")
def health(_: dict = Depends(require_admin)):
    require_feature("orders.read")
    return {"status": "ok", "router": "admin_orders_routes", "prefix": "/api/v1/admin"}
