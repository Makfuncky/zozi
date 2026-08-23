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

from domains.governance.events import publish_gov_order_bulk_delete_requested







from domains.governance.events import publish_gov_order_bulk_status_update_requested



from domains.catalog.admin_promotions_service import create_coupon



from domains.orders.customer_coupons_create_service import delete_coupon

from domains.governance.events import publish_gov_order_delete_requested



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

from domains.finance.services.payments.payout_approval_read_service import list_pending_payouts

from domains.governance.services.users.users_service_accounts import list_staff_accounts

from domains.comms.services.ticket.tickets_service import list_tickets

from domains.governance.events import publish_gov_order_refund_requested

from domains.catalog.admin_products_service import reject_product


from domains.comms.services.ticket.tickets_service import reply_to_ticket


from domains.governance.services.admin_controller import require_admin_2fa_verified

from domains.governance.services.permissions.effective_permissions import require_permission




from domains.orders.services.coupons_write_service import update_coupon

from domains.governance.events import publish_gov_order_status_update_requested

from domains.governance.events import publish_gov_order_tracking_update_requested



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







@router.get("/orders", response_model=ListPage[OrderSchema])

def list_orders(

    limit: Optional[int] = Query(100, ge=1, le=500),

    offset: int = Query(0, ge=0),

    search: Optional[str] = Query(None),

    status: Optional[str] = Query(None),

    date_range: Optional[str] = Query(None),

    min_amount: Optional[float] = Query(None),

    max_amount: Optional[float] = Query(None),

    missing_tracking_only: bool = Query(False),

    db: Session = Depends(get_db),

    current_admin: dict = Depends(get_current_admin),

):

    require_permission("orders.manage", current_admin)

    return get_all_orders(

        db,

        limit=limit,

        offset=offset,

        search=search,

        status=status,

        date_range=date_range,

        min_amount=min_amount,

        max_amount=max_amount,

        missing_tracking_only=missing_tracking_only,

    )







@router.post("/orders/bulk-status")

def bulk_update_orders_status(

    body: BulkOrderStatusBody,

    db: Session = Depends(get_db),

    current_admin: dict = Depends(get_current_admin),

):

    """Bulk-update order status for up to 200 orders."""

    require_permission("orders.manage", current_admin)

    return publish_gov_order_bulk_status_update_requested(body.order_ids, body.status, current_admin, db)







@router.delete("/orders/bulk")

def bulk_delete_orders(

    body: BulkOrderDeleteBody,

    db: Session = Depends(get_db),

    current_admin: dict = Depends(require_admin_2fa_verified),

):

    """Bulk hard-delete orders (admin only, up to 100). Requires 2FA verification."""

    require_permission("orders.manage", current_admin)

    return publish_gov_order_bulk_delete_requested(body.order_ids, current_admin, db)





@router.delete("/orders/{order_id}")

def delete_order_route(

    order_id: int,

    db: Session = Depends(get_db),

    current_admin: dict = Depends(require_admin_2fa_verified),

):

    """Delete a single order. Requires 2FA verification."""

    require_permission("orders.manage", current_admin)

    return publish_gov_order_delete_requested(order_id, current_admin, db)





@router.put("/orders/{order_id}/status")

def set_order_status(

    order_id: int,

    status: str,

    db: Session = Depends(get_db),

    current_admin: dict = Depends(get_current_admin),

):

    require_permission("orders.manage", current_admin)

    return publish_gov_order_status_update_requested(order_id, status, current_admin, db)





@router.post("/orders/{order_id}/refund")

def refund_order_route(

    order_id: int,

    db: Session = Depends(get_db),

    current_admin: dict = Depends(require_admin_2fa_verified),

):

    """Process a refund for an order. Requires 2FA verification."""

    require_permission("orders.manage", current_admin)

    return publish_gov_order_refund_requested(order_id, current_admin, db)





@router.put("/orders/{order_id}/tracking")

def set_order_tracking(

    order_id: int,

    tracking_number: str,

    db: Session = Depends(get_db),

    current_admin: dict = Depends(get_current_admin),

):

    require_permission("orders.manage", current_admin)

    return publish_gov_order_tracking_update_requested(order_id, tracking_number, current_admin, db)





# ── Products ───────────────────────────────────────────────────────────────────
