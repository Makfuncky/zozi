from domains.governance.events import publish_gov_bulk_manage_suppliers_requested
from domains.governance.events import publish_gov_bulk_supplier_verification_requested
from domains.governance.events import publish_gov_reject_supplier_requested
from domains.governance.events import publish_gov_verify_supplier_requested
"""

Admin Router — route declarations only (HTTP layer).

All business logic lives in controllers/admin_controller.py.

"""

from datetime import datetime

from typing import List, Optional



from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query

from fastapi.responses import JSONResponse

from pydantic import BaseModel, field_validator

from sqlalchemy.orm import Session



from domains.orders.services import disputes_controller

from domains.catalog.admin_products_service import approve_product











from domains.catalog.admin_promotions_service import create_coupon



from domains.orders.customer_coupons_create_service import delete_coupon




from domains.governance.services.user.identity_admin_service import delete_user_admin


from domains.governance.services.orders.orders_service import get_all_orders

from domains.governance.services.products.products_service import get_all_products

from domains.governance.services.suppliers.suppliers_service import get_all_suppliers

from domains.governance.services.users.users_service_accounts import get_all_users

from domains.governance.services.analytics.analytics_service import get_analytics

from domains.governance.services.analytics.analytics_service import get_analytics_timeseries

from domains.governance.services.settings.misc_service import get_audit_log_page

from domains.governance.services.settings.misc_service import get_available_audit_actions

from domains.governance.services.analytics.analytics_service import get_chatbot_analytics



from domains.governance.services.analytics.analytics_service import get_customer_insights

from domains.governance.services.settings.database_service import get_database_overview

from domains.governance.services.permissions.permissions_service import get_hierarchy_permissions

from domains.governance.services.products.products_service import get_pending_products

from domains.governance.services.suppliers.suppliers_service import get_pending_suppliers

from domains.governance.services.permissions.permissions_service import get_staff_permission_catalog

from domains.governance.services.suppliers.suppliers_service import get_supplier_comparison

from domains.governance.services.admin_controller import get_ticket_detail

from domains.governance.services.analytics.analytics_service import get_top_products_analytics

from domains.governance.services.analytics.analytics_service import get_user_growth_analytics

from domains.orders.customer_coupons_create_service import list_coupons

from domains.governance.services.users.users_service_accounts import list_pending_bank_accounts

from domains.finance.services.payouts.payout_approval_read_service import list_pending_payouts

from domains.governance.services.users.users_service_accounts import list_staff_accounts

from domains.comms.services.ticket.tickets_service import list_tickets


from domains.catalog.admin_products_service import reject_product


from domains.comms.services.ticket.tickets_service import reply_to_ticket


from domains.governance.services.admin_controller import require_admin_2fa_verified

from domains.governance.services.permissions.effective_permissions import require_permission




from domains.orders.services.coupons_write_service import update_coupon





from domains.comms.services.ticket.tickets_write_service import update_ticket_status


from domains.hr.payroll_service import verify_bank_account

from domains.logistics.logistics_partner_service import verify_payout


from domains.catalog.services.banner_controller import BannerCreate

from domains.catalog.services.banner_controller import BannerUpdate

from domains.catalog.services.banner_controller import create_banner

from domains.catalog.services.banner_controller import delete_banner

from domains.catalog.services.banner_controller import get_banner_by_id

from domains.catalog.services.banner_controller import update_banner

from domains.governance.core.export_service import (

    download_export_job_result,

    export_audit_logs_csv,

    export_coupons_csv,

    export_orders_csv,

    export_products_csv,

    export_transfer_csv,

    export_users_csv,

    queue_export_job,

)

from domains.orders.services.promotion_controller import create_promotion_tier

from domains.orders.services.promotion_controller import delete_promotion_tier

from domains.orders.services.promotion_controller import get_promotion_config

from domains.orders.services.promotion_controller import list_promotion_tiers

from domains.orders.services.promotion_controller import preview_order_tier_discount

from domains.orders.services.promotion_controller import update_promotion_config

from domains.orders.services.promotion_controller import update_promotion_tier

from infrastructure.database.database import get_db

from infrastructure.database.schemas import (

    AuditLogPage,

    BulkUpdateStaffBody,

    CouponSchema,

    CreateStaffAccount,

    ListPage,

    UpdateStaffAccount,

)

from infrastructure.database.schemas import (

    Order as OrderSchema,

)

from infrastructure.database.schemas import (

    Product as ProductSchema,

)

from domains.governance.core.approval_matrix_service import APPROVAL_RULES

from domains.governance.core.approval_matrix_service import can_approve

from domains.governance.core.approval_matrix_service import get_approval_chain

from domains.governance.core.approval_matrix_service import require_approval

from domains.governance.core.approval_matrix_service import resolve_approvers

from domains.hr.hierarchy_service import backfill_authority_levels

from domains.hr.hierarchy_service import get_all_subordinates

from domains.hr.hierarchy_service import get_authority_level

from domains.hr.hierarchy_service import get_org_chart

from domains.hr.hierarchy_service import get_team_members

from domains.hr.hierarchy_service import get_user_chain

from domains.hr.hierarchy_service import is_in_chain

from domains.hr.hierarchy_service import reassign_manager

from domains.hr.hierarchy_service import can_manage as hierarchy_can_manage_service

from domains.comms.services.utility.misc_write_service import reset_demo_data

from infrastructure.utils.backup import get_backup_manager

from infrastructure.utils.constants import MAX_BULK_ITEMS








# ── Users ──────────────────────────────────────────────────────────────────────



from domains.orders.services.flash_sale_controller import create_flash_sale
from domains.orders.services.flash_sale_controller import delete_flash_sale
from domains.orders.services.flash_sale_controller import get_all_flash_sales
from domains.orders.services.flash_sale_controller import update_flash_sale
from infrastructure.database.schemas import FlashSaleCreate, FlashSaleOut
from infrastructure.config import settings
from rbac.dependencies import require_feature, require_module
from modules.admin.auth import get_current_admin, get_current_user, require_admin

router = APIRouter(dependencies=[Depends(require_module("admin"))])


class BulkDeleteUsersBody(BaseModel):

    user_ids: List[int]



    @field_validator("user_ids")

    @classmethod

    def limit_bulk_size(cls, v: List[int]) -> List[int]:

        if len(v) > MAX_BULK_ITEMS:

            raise ValueError(f"Cannot process more than {MAX_BULK_ITEMS} items at once")

        return v





class BulkToggleActiveBody(BaseModel):

    user_ids: List[int]

    is_active: bool



    @field_validator("user_ids")

    @classmethod

    def limit_bulk_size(cls, v: List[int]) -> List[int]:

        if len(v) > MAX_BULK_ITEMS:

            raise ValueError(f"Cannot process more than {MAX_BULK_ITEMS} items at once")

        return v





class BulkUserRoleBody(BaseModel):

    user_ids: List[int]

    role: str



    @field_validator("user_ids")

    @classmethod

    def limit_bulk_size(cls, v: List[int]) -> List[int]:

        if len(v) > MAX_BULK_ITEMS:

            raise ValueError(f"Cannot process more than {MAX_BULK_ITEMS} items at once")

        return v





class ResetPasswordBody(BaseModel):

    new_password: str





class BulkOrderStatusBody(BaseModel):

    order_ids: List[int]

    status: str



    @field_validator("order_ids")

    @classmethod

    def limit_bulk_size(cls, v: List[int]) -> List[int]:

        if len(v) > MAX_BULK_ITEMS:

            raise ValueError(f"Cannot process more than {MAX_BULK_ITEMS} items at once")

        return v





class BulkOrderDeleteBody(BaseModel):

    order_ids: List[int]



    @field_validator("order_ids")

    @classmethod

    def limit_bulk_size(cls, v: List[int]) -> List[int]:

        if len(v) > MAX_BULK_ITEMS:

            raise ValueError(f"Cannot process more than {MAX_BULK_ITEMS} items at once")

        return v





class BulkProductDeleteBody(BaseModel):

    product_ids: List[int]



    @field_validator("product_ids")

    @classmethod

    def limit_bulk_size(cls, v: List[int]) -> List[int]:

        if len(v) > MAX_BULK_ITEMS:

            raise ValueError(f"Cannot process more than {MAX_BULK_ITEMS} items at once")

        return v





class BulkProductModerationBody(BaseModel):

    product_ids: List[int]

    action: str  # "approve" | "reject"

    note: Optional[str] = None



    @field_validator("product_ids")

    @classmethod

    def limit_bulk_size(cls, v: List[int]) -> List[int]:

        if len(v) > MAX_BULK_ITEMS:

            raise ValueError(f"Cannot process more than {MAX_BULK_ITEMS} items at once")

        return v





class BulkSupplierVerifyBody(BaseModel):

    supplier_ids: List[int]

    action: str  # "verify" | "reject"

    note: Optional[str] = None



    @field_validator("supplier_ids")

    @classmethod

    def limit_bulk_size(cls, v: List[int]) -> List[int]:

        if len(v) > MAX_BULK_ITEMS:

            raise ValueError(f"Cannot process more than {MAX_BULK_ITEMS} items at once")

        return v





class BulkSupplierLifecycleBody(BaseModel):

    supplier_ids: List[int]

    action: str

    note: Optional[str] = None

    badge_level: Optional[str] = None



    @field_validator("supplier_ids")

    @classmethod

    def limit_bulk_size(cls, v: List[int]) -> List[int]:

        if len(v) > MAX_BULK_ITEMS:

            raise ValueError(f"Cannot process more than {MAX_BULK_ITEMS} items at once")

        return v





class PromotionConfigBody(BaseModel):

    engine_enabled: Optional[bool] = None

    allow_product_coupons: Optional[bool] = None

    allow_category_coupons: Optional[bool] = None

    allow_order_tier_discounts: Optional[bool] = None

    allow_referral_rewards: Optional[bool] = None

    allow_supplier_promotions: Optional[bool] = None

    allow_global_coupons: Optional[bool] = None

    stacking_mode: Optional[str] = None

    max_combined_discount_percent: Optional[float] = None

    max_combined_discount_amount: Optional[float] = None

    show_savings_line_item: Optional[bool] = None

    tier_discount_visible: Optional[bool] = None

    points_per_omr: Optional[int] = None

    referral_referrer_points: Optional[int] = None

    referral_referee_points: Optional[int] = None

    points_expiry_months: Optional[int] = None

    referral_monthly_cap: Optional[int] = None

    referral_verification_delay_days: Optional[int] = None

    min_points_redeem: Optional[int] = None

    allow_partial_points_redemption: Optional[bool] = None







class PromotionTierBody(BaseModel):

    tier_name: str

    min_order: float

    max_order: Optional[float] = None

    discount_type: str

    discount_value: float

    stacking_allowed: bool = False

    is_active: bool = True

    sort_order: int = 0







class PromotionTierUpdateBody(BaseModel):

    tier_name: Optional[str] = None

    min_order: Optional[float] = None

    max_order: Optional[float] = None

    discount_type: Optional[str] = None

    discount_value: Optional[float] = None

    stacking_allowed: Optional[bool] = None

    is_active: Optional[bool] = None

    sort_order: Optional[int] = None







class PromotionPreviewBody(BaseModel):

    order_subtotal: float

    coupon_discount: float = 0.0







class AdminDisputeBulkActionBody(BaseModel):

    dispute_ids: List[int]

    action: str

    value: Optional[str] = None



    @field_validator("dispute_ids")

    @classmethod

    def limit_bulk_size(cls, v: List[int]) -> List[int]:

        if len(v) > MAX_BULK_ITEMS:

            raise ValueError(f"Cannot process more than {MAX_BULK_ITEMS} items at once")

        return v







class UpdateRolePermissionsIn(BaseModel):

    permissions: List[str]





class ReassignManagerBody(BaseModel):

    user_id: int

    new_manager_id: int | None = None







class ResourceApprovalCheckIn(BaseModel):

    resource_type: str

    amount: Optional[float] = None







@router.post("/suppliers/bulk-verify")

def bulk_verify_suppliers(

    body: BulkSupplierVerifyBody,

    db: Session = Depends(get_db),

    current_admin: dict = Depends(get_current_admin),

):

    """Bulk verify or reject supplier accounts."""

    require_permission("moderation.suppliers", current_admin)

    return publish_gov_bulk_supplier_verification_requested(body.supplier_ids, body.action, body.note, current_admin, db)







@router.post("/suppliers/v1/bulk")

def bulk_manage_supplier_lifecycle(

    body: BulkSupplierLifecycleBody,

    db: Session = Depends(get_db),

    current_admin: dict = Depends(get_current_admin),

):

    """Bulk supplier lifecycle actions: verify/reject/activate/suspend/delete."""

    require_permission("moderation.suppliers", current_admin)

    return publish_gov_bulk_manage_suppliers_requested(body.supplier_ids, body.action, body.note, current_admin, db, badge_level=body.badge_level)





@router.get("/suppliers/v1/comparison", response_model=ListPage[dict])

def supplier_comparison(

    page: int = Query(1, ge=1),

    page_size: int = Query(100, ge=1, le=500),

    db: Session = Depends(get_db),

    current_admin: dict = Depends(get_current_admin),

):

    """Compare all suppliers by products, orders, and revenue."""

    require_permission("analytics.view", current_admin)

    return get_supplier_comparison(db, limit=page_size, offset=(page - 1) * page_size)





# ── Customer Insights ──────────────────────────────────────────────────────────





@router.get("/suppliers/pending", response_model=ListPage[dict])

def list_pending_suppliers(

    page: int = Query(1, ge=1),

    page_size: int = Query(200, ge=1, le=500),

    db: Session = Depends(get_db),

    current_admin: dict = Depends(get_current_admin),

):

    """List all suppliers awaiting verification."""

    require_permission("moderation.suppliers", current_admin)

    return get_pending_suppliers(db, limit=page_size, offset=(page - 1) * page_size)





@router.post("/suppliers/{user_id}/verify")

def approve_supplier(

    user_id: int,

    note: Optional[str] = Body(None),

    db: Session = Depends(get_db),

    current_admin: dict = Depends(get_current_admin),

):

    """Approve a supplier's KYC/verification request."""

    require_permission("moderation.suppliers", current_admin)

    require_approval(db, current_admin["id"], "supplier")

    return publish_gov_verify_supplier_requested(user_id, note, current_admin, db)





@router.post("/suppliers/{user_id}/reject")

def decline_supplier(

    user_id: int,

    note: Optional[str] = Body(None),

    db: Session = Depends(get_db),

    current_admin: dict = Depends(get_current_admin),

):

    """Reject a supplier's verification request."""

    require_permission("moderation.suppliers", current_admin)

    require_approval(db, current_admin["id"], "supplier")

    return publish_gov_reject_supplier_requested(user_id, note, current_admin, db)





@router.put("/suppliers/{user_id}/badge")

def set_supplier_badge(

    user_id: int,

    badge_level: str,

    db: Session = Depends(get_db),

    current_admin: dict = Depends(get_current_admin),

):

    """Admin: manually set a supplier's credibility badge level."""

    require_permission("moderation.suppliers", current_admin)

    import domains.suppliers.services.supplier_controller as _sc

    return _sc.admin_set_supplier_badge(user_id, badge_level, current_admin, db)





@router.post("/suppliers/{user_id}/refresh-badge")

def refresh_supplier_badge(

    user_id: int,

    db: Session = Depends(get_db),

    current_admin: dict = Depends(get_current_admin),

):

    """Admin: recompute a supplier's credibility score and auto-assign badge."""

    require_permission("moderation.suppliers", current_admin)

    import domains.suppliers.services.supplier_controller as _sc

    return _sc.refresh_supplier_badge(user_id, db)







@router.get("/suppliers/v1/documents", response_model=ListPage[dict])

def admin_supplier_documents(

    supplier_id: Optional[int] = Query(None),

    status: Optional[str] = Query(None),

    doc_type: Optional[str] = Query(None),

    page: int = Query(1, ge=1),

    page_size: int = Query(200, ge=1, le=500),

    db: Session = Depends(get_db),

    current_admin: dict = Depends(get_current_admin),

):

    """Admin: view all supplier KYC documents."""

    require_permission("moderation.suppliers", current_admin)

    import domains.suppliers.services as _sdc

    return _sdc.admin_list_documents(

        current_admin,

        db,

        supplier_id=supplier_id,

        status=status,

        doc_type=doc_type,

        limit=page_size,

        offset=(page - 1) * page_size,

    )





@router.put("/suppliers/v1/documents/{doc_id}/review")

def admin_review_document(

    doc_id: int,

    data: dict,

    db: Session = Depends(get_db),

    current_admin: dict = Depends(get_current_admin),

):

    """Admin: approve or reject a supplier document."""

    require_permission("moderation.suppliers", current_admin)

    import domains.suppliers.services as _sdc

    return _sdc.admin_review_document(doc_id, data, current_admin, db)





# ── Admin Invoices Overview ────────────────────────────────────────────────────





@router.get("/suppliers/v1/all")

def list_all_suppliers(

    page: int = Query(1, ge=1),

    page_size: Optional[int] = Query(None, ge=1, le=200),

    skip: int = 0,

    limit: int | None = None,

    q: Optional[str] = Query(None),

    status: Optional[str] = Query(None),

    badge: Optional[str] = Query(None),

    db: Session = Depends(get_db),

    current_admin: dict = Depends(get_current_admin),

):

    """Admin: list all suppliers with profile summary."""

    require_permission("moderation.suppliers", current_admin)

    resolved_limit = page_size if page_size is not None else limit

    resolved_skip = max(0, skip)

    if page_size is not None:

        resolved_skip = max(0, (page - 1) * page_size)

    return get_all_suppliers(

        db,

        skip=resolved_skip,

        limit=resolved_limit,

        q=q,

        status=status,

        badge=badge,

    )





# ── Banners ────────────────────────────────────────────────────────────────────
