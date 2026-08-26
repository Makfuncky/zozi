from __future__ import annotations

"""Admin orders router — canonical."""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status

from domains.accounts.models.user import User
from modules.admin.routers.governance import archive_entity, restore_entity, bulk_archive_entities, bulk_restore_entities, hard_delete_entity, update_order_status
from infrastructure.database.database import get_db
from infrastructure.database.schemas import OrderOut, OrderStatusUpdate, ArchiveRequest, BulkActionRequest, BulkStatusUpdateRequest
from domains.comms.services._auto_stubs import email_metrics
from domains.country.utils.country_rls import get_country_or_404
from domains.governance.models.user import User
from domains.orders.services._auto_stubs import bulk_delete_orders_route
from domains.orders.services._auto_stubs import create_coupon_route
from domains.orders.services._auto_stubs import delete_coupon_route
from domains.orders.services._auto_stubs import list_coupons_route
from domains.orders.services._auto_stubs import refund_order_route
from domains.orders.services._auto_stubs import update_coupon_route
from domains.orders.services._auto_stubs import update_order_tracking_route
from domains.orders.services.core.admin_extra import create_campaign
from domains.orders.services.core.admin_extra import delete_campaign
from domains.orders.services.core.admin_extra import list_all_campaigns
from domains.orders.services.core.admin_extra import list_campaigns
from infrastructure.database.database import get_db
from infrastructure.database.schemas import EmailCampaignCreate, EmailCampaignOut
from infrastructure.utils.dependencies import require_admin
from infrastructure.utils.rls_interceptor import set_rls_context, clear_rls_context
from sqlalchemy.orm import Session
from typing import Optional
from infrastructure.utils.audit import audit_log
from domains.country.utils.country_rls import enforce_country_access, get_country_or_404
from infrastructure.utils.dependencies import require_admin, require_super_admin
from infrastructure.database.rls_interceptor import clear_rls_context
from infrastructure.database.rls_interceptor import set_rls_context
import modules.admin.routers.orders.orders_controller as _ctrl
import domains.orders.services.orders_controller as _ctrl
import logging as _l; _l.getLogger(__name__).warning("skip cart_router: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip disputes_router: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip orders_router: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip returns_router: %s", _e)
import math

router = APIRouter(prefix="/api/v1/admin/orders", tags=["admin", "orders"])

@router.get("/coupons/{country_code}", status_code=200, tags=['admin-coupons'])
def list_coupons_route_route(
    country_code: str,
    search: Optional[str] = Query(None),
    page: int = Query(1),
    page_size: int = Query(50),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)


@router.post("/coupons/{country_code}", status_code=201, tags=['admin-coupons'])
def create_coupon_route_route(
    country_code: str,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    code: str = Body('', embed=True),
    title: Optional[str] = Body(None, embed=True),
    description: Optional[str] = Body(None, embed=True),
    discount_type: str = Body('percentage', embed=True),
    discount_value: float = Body(0, embed=True),
    maximum_discount: Optional[float] = Body(None, embed=True),
    minimum_order: float = Body(0, embed=True),
    usage_limit: Optional[int] = Body(None, embed=True),
    per_user_limit: Optional[int] = Body(None, embed=True),
    is_active: bool = Body(True, embed=True),
    starts_at: Optional[str] = Body(None, embed=True),
    expires_at: Optional[str] = Body(None, embed=True)


@router.put("/coupons/{country_code}/{coupon_id}", status_code=200, tags=['admin-coupons'])
def update_coupon_route_route(
    country_code: str,
    coupon_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    code: Optional[str] = Body(None, embed=True),
    title: Optional[str] = Body(None, embed=True),
    description: Optional[str] = Body(None, embed=True),
    discount_type: Optional[str] = Body(None, embed=True),
    discount_value: Optional[float] = Body(None, embed=True),
    maximum_discount: Optional[float] = Body(None, embed=True),
    minimum_order: Optional[float] = Body(None, embed=True),
    usage_limit: Optional[int] = Body(None, embed=True),
    per_user_limit: Optional[int] = Body(None, embed=True),
    is_active: Optional[bool] = Body(None, embed=True),
    starts_at: Optional[str] = Body(None, embed=True),
    expires_at: Optional[str] = Body(None, embed=True)


@router.delete("/coupons/{country_code}/{coupon_id}", status_code=200, tags=['admin-coupons'])
def delete_coupon_route_route(
    country_code: str,
    coupon_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)


@router.post("/orders/{country_code}/{order_id}/refund", status_code=201, tags=['admin-orders'])
def refund_order_route_route(
    country_code: str,
    order_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)


@router.put("/orders/{country_code}/{order_id}/tracking", status_code=200, tags=['admin-orders'])
def update_order_tracking_route_route(
    country_code: str,
    order_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    tracking_number: str = Body('')


@router.post("/orders/{country_code}/bulk/delete", status_code=201, tags=['admin-orders'])
def bulk_delete_orders_route_route(
    country_code: str,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    ids: list[int] = Body(None)


@router.get("/campaigns", response_model=list[EmailCampaignOut])
def list_all_campaigns_route(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    """List all email campaigns across all countries (consolidated view)."""
    return list_all_campaigns(db)




@router.get("/metrics")
def admin_email_metrics(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Consolidated email metrics across all countries."""
    return email_metrics(db)




@router.get("/campaigns/{country_code}")
def list_campaigns_route(country_code: str = Path(..., description="ISO country code"), _: User = Depends(require_admin), db: Session = Depends(get_db), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return list_campaigns(db, country_code, page, page_size)
    finally:
        clear_rls_context()




@router.post("/campaigns/{country_code}", response_model=EmailCampaignOut, status_code=201)
def create_campaign_route(country_code: str = Path(..., description="ISO country code"), payload: EmailCampaignCreate = None, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return create_campaign(db, payload, country_code)
    finally:
        clear_rls_context()




@router.delete("/campaigns/{country_code}/{campaign_id}")
def delete_campaign_route(country_code: str = Path(..., description="ISO country code"), campaign_id: int = Path(...), _: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return delete_campaign(db, campaign_id, country_code)
    finally:
        clear_rls_context()



@router.get("/admin_orders_routes/health")
def health():
    """Liveness probe for this router."""
    return {"status": "ok", "router": "admin_orders_routes", "prefix": "/api/v1/admin"}




@router.get("/admin_orders_routes/status")
def status():
    """Report whether a backing controller is importable."""
    return {"router": "admin_orders_routes", "controller": "controllers.orders.orders_controller" if _HAS_CTRL else None,
            "public_functions": _CTRL_PUBLIC}



@router.get("/admin_orders_routes/health")
def health():
    """Liveness probe for this router."""
    return {"status": "ok", "router": "admin_orders_routes", "prefix": "/api/v1/admin"}




@router.get("/admin_orders_routes/status")
def status():
    """Report whether a backing controller is importable."""
    return {"router": "admin_orders_routes", "controller": "controllers.orders.orders_controller" if _HAS_CTRL else None,
            "public_functions": _CTRL_PUBLIC}



@router.get("/orders/{country_code}")
def list_all_orders(
    country_code: str = Path(..., description="ISO country code, or '*' for all"),
    page: int = Query(1, ge=1),
    size: int = Query(50),
    status: str = None,
    include_deleted: bool = False,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),


@router.put("/orders/{country_code}/{order_id}/status")
def update_status(
    country_code: str = Path(..., description="ISO country code"),
    order_id: int = Path(...),
    payload: OrderStatusUpdate = ...,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),


@router.post("/orders/{country_code}/{order_id}/archive")
def archive_order(
    country_code: str = Path(..., description="ISO country code"),
    order_id: int = Path(...),
    payload: ArchiveRequest = None,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),


@router.post("/orders/{country_code}/{order_id}/restore")
def restore_order(
    country_code: str = Path(..., description="ISO country code"),
    order_id: int = Path(...),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),


@router.post("/orders/{country_code}/bulk/archive")
def bulk_archive_orders(
    country_code: str = Path(..., description="ISO country code"),
    payload: BulkActionRequest = ...,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),


@router.post("/orders/{country_code}/bulk/restore")
def bulk_restore_orders(
    country_code: str = Path(..., description="ISO country code"),
    payload: BulkActionRequest = ...,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),


@router.post("/orders/{country_code}/bulk/status")
def bulk_update_order_status(
    country_code: str = Path(..., description="ISO country code"),
    payload: BulkStatusUpdateRequest = ...,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),


@router.delete("/orders/{country_code}/{order_id}")
def delete_order_permanent(
    country_code: str = Path(..., description="ISO country code"),
    order_id: int = Path(...),
    _: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),


@router.get("/store_orders_routes/health")
def health():
    """Liveness probe for this router."""
    return {"status": "ok", "router": "store_orders_routes", "prefix": "/api/v1/orders"}




@router.get("/store_orders_routes/status")
def status():
    """Report whether a backing controller is importable."""
    return {"router": "store_orders_routes", "controller": "controllers.orders.orders_controller" if _HAS_CTRL else None,
            "public_functions": _CTRL_PUBLIC}


