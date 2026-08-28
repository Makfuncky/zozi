from __future__ import annotations

"""Admin orders router — canonical."""

from fastapi import APIRouter, Depends, Query, Path, Body, HTTPException, status
from sqlalchemy.orm import Session

from infrastructure.database.database import get_db
from infrastructure.security.dependencies import require_admin
from rbac.dependencies import require_feature
from domains.comms.ports import (
    create_campaign,
    delete_campaign,
    list_all_campaigns,
    list_campaigns,
)
from domains.country.ports import get_country_or_404
router = APIRouter(prefix="/api/v1/admin/orders", tags=["admin", "orders"])


@router.get("/campaigns", status_code=200)
def list_all_campaigns_route(_: dict = Depends(require_admin), db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("orders.list"))
):
    return list_all_campaigns(db)


@router.get("/metrics")
def admin_email_metrics(_: dict = Depends(require_admin), db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("orders.read"))
):
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
    _rf_gate: None = Depends(require_feature("orders.list")),
):
    get_country_or_404(country_code.upper(), db)
    return list_campaigns(db, country_code, page, page_size)


@router.post("/campaigns/{country_code}", status_code=201)
def create_campaign_route(
    country_code: str = Path(..., description="ISO country code"),
    payload: dict = Body(...),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("orders.create")),
):
    get_country_or_404(country_code.upper(), db)
    return create_campaign(db, payload, country_code)


@router.delete("/campaigns/{country_code}/{campaign_id}")
def delete_campaign_route(
    country_code: str = Path(..., description="ISO country code"),
    campaign_id: int = Path(...),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("orders.manage")),
):
    get_country_or_404(country_code.upper(), db)
    return delete_campaign(db, campaign_id, country_code)


@router.get("/admin_orders_routes/health")
def health(_: dict = Depends(require_admin),
    _rf_gate: None = Depends(require_feature("orders.read"))
):
    return {"status": "ok", "router": "admin_orders_routes", "prefix": "/api/v1/admin"}
