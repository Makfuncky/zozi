"""Admin promotions router — canonical."""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status

from .banners import router as banners_router
from .bogo import router as bogo_router
from .coupons import router as coupons_router
from __future__ import annotations
from domains.accounts.services._auto_stubs import get_hierarchy_permissions
from domains.accounts.services._auto_stubs import get_staff_permission_catalog
from domains.accounts.services.identity.identity_admin_service import delete_user_admin
from domains.accounts.services.users.users_admin_service import get_all_users
from domains.accounts.services.users.users_admin_service import list_pending_bank_accounts
from domains.accounts.services.users.users_admin_service import list_staff_accounts
from domains.accounts.services.users.users_admin_service import verify_bank_account
from domains.analytics.services.analytics_service__analytics import get_analytics
from domains.analytics.services.analytics_service__analytics import get_analytics_timeseries
from domains.analytics.services.analytics_service__analytics import get_chatbot_analytics
from domains.analytics.services.analytics_service__analytics import get_customer_insights
from domains.analytics.services.analytics_service__analytics import get_top_products_analytics
from domains.analytics.services.analytics_service__analytics import get_user_growth_analytics
from domains.catalog.services._auto_stubs import upload_banner_image
from domains.catalog.services.products.admin_products_service import approve_product
from domains.catalog.services.products.admin_products_service import get_all_products
from domains.catalog.services.products.admin_products_service import reject_product
from domains.comms.services.shared.utility.shared_utils import reset_demo_data
from domains.comms.services.tickets.tickets_service import list_tickets
from domains.comms.services.tickets.tickets_service import update_ticket_status
from domains.country.utils.country_rls import get_country_or_404
from domains.customers.services.coupons_read_service import list_coupons
from domains.customers.services.coupons_service import create_coupon
from domains.customers.services.coupons_service import delete_coupon
from domains.customers.services.coupons_write_service import update_coupon
from domains.finance.services.payouts.payout_batch_service import list_pending_payouts
from domains.finance.services.payouts.payout_batch_service import verify_payout
from domains.governance.core.export_service import (
from domains.governance.models.user import User
from domains.governance.services._auto_stubs import APPROVAL_RULES
from domains.governance.services._auto_stubs import get_all_suppliers
from domains.governance.services._auto_stubs import get_pending_products
from domains.governance.services._auto_stubs import get_pending_suppliers
from domains.governance.services._auto_stubs import get_supplier_comparison
from domains.governance.services._auto_stubs import get_ticket_detail
from domains.governance.services._auto_stubs import require_admin_2fa_verified
from domains.governance.services.approval.approval_matrix_service import can_approve
from domains.governance.services.approval.approval_matrix_service import get_approval_chain
from domains.governance.services.approval.approval_matrix_service import require_approval
from domains.governance.services.approval.approval_matrix_service import resolve_approvers
from domains.governance.services.settings.misc_service import get_audit_log_page
from domains.governance.services.settings.misc_service import get_available_audit_actions
from domains.hr.services.hierarchy.hierarchy_service import backfill_authority_levels
from domains.hr.services.hierarchy.hierarchy_service import can_manage as hierarchy_can_manage_service
from domains.hr.services.hierarchy.hierarchy_service import get_all_subordinates
from domains.hr.services.hierarchy.hierarchy_service import get_authority_level
from domains.hr.services.hierarchy.hierarchy_service import get_org_chart
from domains.hr.services.hierarchy.hierarchy_service import get_team_members
from domains.hr.services.hierarchy.hierarchy_service import get_user_chain
from domains.hr.services.hierarchy.hierarchy_service import is_in_chain
from domains.hr.services.hierarchy.hierarchy_service import reassign_manager
from domains.orders.services._auto_stubs import delete_flash_sale
from domains.orders.services._auto_stubs import disputes_controller
from domains.orders.services._auto_stubs import get_all_flash_sales
from domains.orders.services.orders_service import get_all_orders
from domains.promotions.services.admin_promotion_service import create_banner
from domains.promotions.services.admin_promotion_service import create_banner as create_banner_controller
from domains.promotions.services.admin_promotion_service import create_banner_by_country
from domains.promotions.services.admin_promotion_service import create_coupon_by_country
from domains.promotions.services.admin_promotion_service import create_flash_sale
from domains.promotions.services.admin_promotion_service import delete_banner
from domains.promotions.services.admin_promotion_service import delete_banner as delete_banner_controller
from domains.promotions.services.admin_promotion_service import delete_banner_by_country
from domains.promotions.services.admin_promotion_service import get_promotion_config
from domains.promotions.services.admin_promotion_service import list_promotion_tiers
from domains.promotions.services.admin_promotion_service import update_banner
from domains.promotions.services.admin_promotion_service import update_banner as update_banner_controller
from domains.promotions.services.admin_promotion_service import update_banner_by_country
from domains.promotions.services.admin_promotion_service import update_flash_sale
from domains.promotions.services.admin_promotion_service import update_promotion_config
from domains.promotions.services.banners.banner_service import BannerCreate
from domains.promotions.services.banners.banner_service import BannerUpdate
from domains.promotions.services.banners.banner_service import get_banner_by_id
from domains.promotions.services.banners.banner_service import get_banners
from domains.promotions.services.banners.banner_service import get_banners_page
from domains.promotions.services.engine.admin_promotions_write_service import update_config
from domains.promotions.services.engine.promotion_service import create_promotion_tier
from domains.promotions.services.engine.promotion_service import delete_promotion_tier
from domains.promotions.services.engine.promotion_service import preview_order_tier_discount
from domains.promotions.services.engine.promotion_service import update_promotion_tier
from infrastructure.utils.config import settings
from infrastructure.database.database import get_db
from infrastructure.database.database_service import get_database_overview
from infrastructure.database.schemas import (
from infrastructure.database.schemas import FlashSaleCreate, FlashSaleOut
from infrastructure.security.auth import require_permission
from infrastructure.utils.backup import get_backup_manager
from infrastructure.utils.constants import MAX_BULK_ITEMS
from infrastructure.utils.dependencies import require_admin
from infrastructure.utils.operations_service import reply_to_ticket
from infrastructure.utils.rls_interceptor import clear_rls_context, set_rls_context
from infrastructure.utils.rls_interceptor import set_rls_context, clear_rls_context
from modules.admin.auth import get_current_admin, get_current_user, require_admin
from rbac.dependencies import require_feature, require_module
from sqlalchemy.orm import Session
from typing import Any, Optional
from typing import List, Optional
import logging as _l; _l.getLogger(__name__).warning("skip banners_router: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip bogo_router: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip coupons_router: %s", _e)

router = APIRouter(prefix="/api/v1/admin/promotions", tags=["admin", "promotions"])

@router.get("/banners/{country_code}")
def list_banners(country_code: str = Path(..., description="ISO country code"), position: str = None, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return get_banners(db, banner_type=position, active_only=True)
    finally:
        clear_rls_context()




@router.get("/banners/{country_code}/all")
def list_all_banners(country_code: str = Path(..., description="ISO country code"), _: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return get_banners_page(db, active_only=False)
    finally:
        clear_rls_context()




@router.post("/banners/{country_code}")
def create_banner(country_code: str = Path(..., description="ISO country code"), payload: BannerCreate = None, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return create_banner_controller(payload, getattr(admin, "id"), _admin_context(admin), db)
    finally:
        clear_rls_context()




@router.put("/banners/{country_code}/{banner_id}")
def update_banner(country_code: str = Path(..., description="ISO country code"), banner_id: int = Path(...), payload: BannerUpdate = None, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return update_banner_controller(banner_id, payload, _admin_context(admin), db)
    finally:
        clear_rls_context()




@router.post("/banners/{country_code}/{banner_id}/image")
async def upload_image(country_code: str = Path(..., description="ISO country code"), banner_id: int = Path(...), file: UploadFile = File(...), admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return await upload_banner_image(banner_id, file, _admin_context(admin), db)
    finally:
        clear_rls_context()


@router.delete("/banners/{country_code}/{banner_id}")
def delete_banner(country_code: str = Path(..., description="ISO country code"), banner_id: int = Path(...), admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return delete_banner_controller(banner_id, _admin_context(admin), db)
    finally:
        clear_rls_context()




@router.get("/banners/{country_code}")
def list_banners(country_code: str = Path(..., description="ISO country code"), position: str = None, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return get_banners(db, banner_type=position, active_only=True)
    finally:
        clear_rls_context()




@router.get("/banners/{country_code}/all")
def list_all_banners(country_code: str = Path(..., description="ISO country code"), _: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return get_banners_page(db, active_only=False)
    finally:
        clear_rls_context()




@router.post("/banners/{country_code}")
def create_banner(country_code: str = Path(..., description="ISO country code"), payload: BannerCreate = None, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return create_banner_controller(payload, getattr(admin, "id"), _admin_context(admin), db)
    finally:
        clear_rls_context()




@router.put("/banners/{country_code}/{banner_id}")
def update_banner(country_code: str = Path(..., description="ISO country code"), banner_id: int = Path(...), payload: BannerUpdate = None, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return update_banner_controller(banner_id, payload, _admin_context(admin), db)
    finally:
        clear_rls_context()




@router.post("/banners/{country_code}/{banner_id}/image")
async def upload_image(country_code: str = Path(..., description="ISO country code"), banner_id: int = Path(...), file: UploadFile = File(...), admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return await upload_banner_image(banner_id, file, _admin_context(admin), db)
    finally:
        clear_rls_context()


@router.delete("/banners/{country_code}/{banner_id}")
def delete_banner(country_code: str = Path(..., description="ISO country code"), banner_id: int = Path(...), admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return delete_banner_controller(banner_id, _admin_context(admin), db)
    finally:
        clear_rls_context()




@router.put("/promotions/config/{config_id}", status_code=200, tags=['promotions'])
def update_config_route(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
    engine_enabled: Optional[bool] = Body(..., embed=True),
    stacking_mode: Optional[str] = Body(..., embed=True)


@router.post("/promotions/coupons", status_code=201, tags=['promotions'])
def create_coupon_route(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
    code: str = Body(..., embed=True),
    discount_type: str = Body('percentage', embed=True),
    discount_value: float = Body(0, embed=True),
    minimum_order: Optional[float] = Body(None, embed=True),
    maximum_discount: Optional[float] = Body(None, embed=True),
    usage_limit: Optional[int] = Body(None, embed=True),
    starts_at: Optional[str] = Body(None, embed=True),
    expires_at: Optional[str] = Body(None, embed=True),
    is_active: bool = Body(True, embed=True),
    country_code: Optional[str] = Body(None, embed=True)


@router.post("/{code}/coupons", status_code=201, tags=['promotions'])
def create_coupon_by_country_route(
    code: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
    coupon_code: str = Body(..., embed=True),
    discount_type: str = Body('percentage', embed=True),
    discount_value: float = Body(0, embed=True),
    minimum_order: Optional[float] = Body(None, embed=True),
    maximum_discount: Optional[float] = Body(None, embed=True),
    usage_limit: Optional[int] = Body(None, embed=True),
    starts_at: Optional[str] = Body(None, embed=True),
    expires_at: Optional[str] = Body(None, embed=True),
    is_active: bool = Body(True, embed=True)


@router.post("/promotions/flash-sales", status_code=201, tags=['promotions'])
def create_flash_sale_route(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
    title: str = Body(..., embed=True),
    discount_pct: float = Body(..., embed=True),
    starts_at: str = Body(..., embed=True),
    ends_at: str = Body(..., embed=True),
    description: Optional[str] = Body(None, embed=True),
    is_active: bool = Body(True, embed=True),
    country_code: Optional[str] = Body(None, embed=True)


@router.put("/promotions/flash-sales/{sale_id}", status_code=200, tags=['promotions'])
def update_flash_sale_route(
    sale_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
    title: Optional[str] = Body(None, embed=True),
    description: Optional[str] = Body(None, embed=True),
    discount_pct: Optional[float] = Body(None, embed=True),
    starts_at: Optional[str] = Body(None, embed=True),
    ends_at: Optional[str] = Body(None, embed=True),
    is_active: Optional[bool] = Body(None, embed=True),
    country_code: Optional[str] = Body(None, embed=True)


@router.post("/promotions/banners", status_code=201, tags=['promotions'])
def create_banner_route(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
    title: str = Body(..., embed=True),
    subtitle: Optional[str] = Body(None, embed=True),
    image_url: Optional[str] = Body(None, embed=True),
    link: Optional[str] = Body(None, embed=True),
    cta_label: Optional[str] = Body(None, embed=True),
    cta_url: Optional[str] = Body(None, embed=True),
    banner_type: str = Body('hero', embed=True),
    is_active: bool = Body(True, embed=True),
    sort_order: int = Body(0, embed=True),
    bg_color: Optional[str] = Body(None, embed=True),
    text_color: Optional[str] = Body(None, embed=True),
    subtitle_color: Optional[str] = Body(None, embed=True),
    btn_bg_color: Optional[str] = Body(None, embed=True),
    btn_text_color: Optional[str] = Body(None, embed=True),
    badge_text: Optional[str] = Body(None, embed=True),
    badge_color: Optional[str] = Body(None, embed=True),
    effect: Optional[str] = Body(None, embed=True),
    layout_json: Optional[str] = Body(None, embed=True),
    video_url: Optional[str] = Body(None, embed=True),
    country_code: Optional[str] = Body(None, embed=True)


@router.put("/promotions/banners/{banner_id}", status_code=200, tags=['promotions'])
def update_banner_route(
    banner_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
    title: Optional[str] = Body(None, embed=True),
    subtitle: Optional[str] = Body(None, embed=True),
    image_url: Optional[str] = Body(None, embed=True),
    link: Optional[str] = Body(None, embed=True),
    cta_label: Optional[str] = Body(None, embed=True),
    cta_url: Optional[str] = Body(None, embed=True),
    banner_type: Optional[str] = Body(None, embed=True),
    is_active: Optional[bool] = Body(None, embed=True),
    sort_order: Optional[int] = Body(None, embed=True),
    bg_color: Optional[str] = Body(None, embed=True),
    text_color: Optional[str] = Body(None, embed=True),
    subtitle_color: Optional[str] = Body(None, embed=True),
    btn_bg_color: Optional[str] = Body(None, embed=True),
    btn_text_color: Optional[str] = Body(None, embed=True),
    badge_text: Optional[str] = Body(None, embed=True),
    badge_color: Optional[str] = Body(None, embed=True),
    effect: Optional[str] = Body(None, embed=True),
    layout_json: Optional[str] = Body(None, embed=True),
    video_url: Optional[str] = Body(None, embed=True),
    country_code: Optional[str] = Body(None, embed=True)


@router.delete("/promotions/banners/{banner_id}", status_code=200, tags=['promotions'])
def delete_banner_route(
    banner_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
    admin_id: Any = Query(None)


@router.post("/{code}/banners", status_code=201, tags=['promotions'])
def create_banner_by_country_route(
    code: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
    title: str = Body(..., embed=True),
    subtitle: Optional[str] = Body(None, embed=True),
    image_url: Optional[str] = Body(None, embed=True),
    link: Optional[str] = Body(None, embed=True),
    cta_label: Optional[str] = Body(None, embed=True),
    cta_url: Optional[str] = Body(None, embed=True),
    banner_type: str = Body('hero', embed=True),
    is_active: bool = Body(True, embed=True),
    sort_order: int = Body(0, embed=True),
    bg_color: Optional[str] = Body(None, embed=True),
    text_color: Optional[str] = Body(None, embed=True),
    subtitle_color: Optional[str] = Body(None, embed=True),
    btn_bg_color: Optional[str] = Body(None, embed=True),
    btn_text_color: Optional[str] = Body(None, embed=True),
    badge_text: Optional[str] = Body(None, embed=True),
    badge_color: Optional[str] = Body(None, embed=True),
    effect: Optional[str] = Body(None, embed=True),
    layout_json: Optional[str] = Body(None, embed=True),
    video_url: Optional[str] = Body(None, embed=True)


@router.put("/{code}/banners/{banner_id}", status_code=200, tags=['promotions'])
def update_banner_by_country_route(
    code: str,
    banner_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
    title: Optional[str] = Body(None, embed=True),
    subtitle: Optional[str] = Body(None, embed=True),
    image_url: Optional[str] = Body(None, embed=True),
    link: Optional[str] = Body(None, embed=True),
    cta_label: Optional[str] = Body(None, embed=True),
    cta_url: Optional[str] = Body(None, embed=True),
    banner_type: Optional[str] = Body(None, embed=True),
    is_active: Optional[bool] = Body(None, embed=True),
    sort_order: Optional[int] = Body(None, embed=True),
    bg_color: Optional[str] = Body(None, embed=True),
    text_color: Optional[str] = Body(None, embed=True),
    subtitle_color: Optional[str] = Body(None, embed=True),
    btn_bg_color: Optional[str] = Body(None, embed=True),
    btn_text_color: Optional[str] = Body(None, embed=True),
    badge_text: Optional[str] = Body(None, embed=True),
    badge_color: Optional[str] = Body(None, embed=True),
    effect: Optional[str] = Body(None, embed=True),
    layout_json: Optional[str] = Body(None, embed=True),
    video_url: Optional[str] = Body(None, embed=True)


@router.delete("/{code}/banners/{banner_id}", status_code=200, tags=['promotions'])
def delete_banner_by_country_route(
    code: str,
    banner_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
    admin_id: Any = Query(None)


@router.get("/disputes", response_model=ListPage[dict])

def list_admin_disputes(

    status: Optional[str] = Query(None),

    priority: Optional[str] = Query(None),

    supplier_id: Optional[int] = Query(None),

    cursor: Optional[str] = Query(None),

    db: Session = Depends(get_db),

    current_admin: dict = Depends(get_current_admin),



@router.get("/disputes/{dispute_id}")

def get_admin_dispute(

    dispute_id: int,

    db: Session = Depends(get_db),

    current_admin: dict = Depends(get_current_admin),



@router.patch("/disputes/{dispute_id}")

def patch_admin_dispute(

    dispute_id: int,

    payload: dict = Body(default_factory=dict),

    db: Session = Depends(get_db),

    current_admin: dict = Depends(get_current_admin),



@router.post("/disputes/bulk")

def bulk_admin_dispute_action(

    body: AdminDisputeBulkActionBody,

    db: Session = Depends(get_db),

    current_admin: dict = Depends(get_current_admin),


