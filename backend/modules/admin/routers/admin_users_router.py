from domains.governance.events import publish_gov_bulk_delete_users_admin_requested
from domains.governance.events import publish_gov_bulk_toggle_users_active_requested
from domains.governance.events import publish_gov_bulk_update_users_role_requested
from domains.governance.events import publish_gov_force_reset_password_admin_requested
from domains.governance.events import publish_gov_toggle_user_active_requested
from domains.governance.events import publish_gov_update_user_role_requested
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

from domains.catalog.services.products.admin_products_service import approve_product











from domains.customers.services.coupons_service import create_coupon



from domains.customers.services.coupons_service import delete_coupon




from domains.accounts.services.identity.identity_admin_service import delete_user_admin


from domains.orders.services.orders_service import get_all_orders

from domains.catalog.services.products.admin_products_service import get_all_products

from domains.governance.services._auto_stubs import get_all_suppliers

from domains.accounts.services.users.users_admin_service import get_all_users

from domains.analytics.services.analytics_service__analytics import get_analytics

from domains.analytics.services.analytics_service__analytics import get_analytics_timeseries

from domains.governance.services.settings.misc_service import get_audit_log_page

from domains.governance.services.settings.misc_service import get_available_audit_actions

from domains.analytics.services.analytics_service__analytics import get_chatbot_analytics



from domains.analytics.services.analytics_service__analytics import get_customer_insights

from infrastructure.database.database_service import get_database_overview

from domains.governance.services._auto_stubs import get_hierarchy_permissions

from domains.governance.services._auto_stubs import get_pending_products

from domains.governance.services._auto_stubs import get_pending_suppliers

from domains.governance.services._auto_stubs import get_staff_permission_catalog

from domains.governance.services._auto_stubs import get_supplier_comparison

from domains.governance.services._auto_stubs import get_ticket_detail

from domains.analytics.services.analytics_service__analytics import get_top_products_analytics

from domains.analytics.services.analytics_service__analytics import get_user_growth_analytics

from domains.customers.services.coupons_read_service import list_coupons

from domains.accounts.services.users.users_admin_service import list_pending_bank_accounts

from domains.finance.services.payouts.payout_batch_service import list_pending_payouts

from domains.accounts.services.users.users_admin_service import list_staff_accounts

from domains.comms.services.tickets.tickets_service import list_tickets


from domains.catalog.services.products.admin_products_service import reject_product


from infrastructure.utils.operations_service import reply_to_ticket


from domains.governance.services._auto_stubs import require_admin_2fa_verified

from infrastructure.security.auth import require_permission




from domains.customers.services.coupons_write_service import update_coupon





from domains.comms.services.tickets.tickets_service import update_ticket_status


from domains.accounts.services.users.users_admin_service import verify_bank_account

from domains.finance.services.payouts.payout_batch_service import verify_payout


from domains.promotions.services.banners.banner_service import BannerCreate

from domains.promotions.services.banners.banner_service import BannerUpdate

from domains.promotions.services.admin_promotion_service import create_banner

from domains.promotions.services.admin_promotion_service import delete_banner

from domains.promotions.services.banners.banner_service import get_banner_by_id

from domains.promotions.services.admin_promotion_service import update_banner

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

from domains.promotions.services.engine.promotion_service import create_promotion_tier

from domains.promotions.services.engine.promotion_service import delete_promotion_tier

from domains.promotions.services.admin_promotion_service import get_promotion_config

from domains.promotions.services.admin_promotion_service import list_promotion_tiers

from domains.promotions.services.engine.promotion_service import preview_order_tier_discount

from domains.promotions.services.admin_promotion_service import update_promotion_config

from domains.promotions.services.engine.promotion_service import update_promotion_tier

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

from domains.governance.services._auto_stubs import APPROVAL_RULES

from domains.governance.services.approval.approval_matrix_service import can_approve

from domains.governance.services.approval.approval_matrix_service import get_approval_chain

from domains.governance.services.approval.approval_matrix_service import require_approval

from domains.governance.services.approval.approval_matrix_service import resolve_approvers

from domains.hr.services.hierarchy.hierarchy_service import backfill_authority_levels

from domains.hr.services.hierarchy.hierarchy_service import get_all_subordinates

from domains.hr.services.hierarchy.hierarchy_service import get_authority_level

from domains.hr.services.hierarchy.hierarchy_service import get_org_chart

from domains.hr.services.hierarchy.hierarchy_service import get_team_members

from domains.hr.services.hierarchy.hierarchy_service import get_user_chain

from domains.hr.services.hierarchy.hierarchy_service import is_in_chain

from domains.hr.services.hierarchy.hierarchy_service import reassign_manager

from domains.hr.services.hierarchy.hierarchy_service import can_manage as hierarchy_can_manage_service

from domains.comms.services.shared.utility.shared_utils import reset_demo_data

from infrastructure.utils.backup import get_backup_manager

from infrastructure.utils.constants import MAX_BULK_ITEMS








# ── Users ──────────────────────────────────────────────────────────────────────



from domains.promotions.services.admin_promotion_service import create_flash_sale
from domains.orders.services._auto_stubs import delete_flash_sale
from domains.orders.services._auto_stubs import get_all_flash_sales
from domains.promotions.services.admin_promotion_service import update_flash_sale
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







@router.get("/users", response_model=ListPage[dict])

def list_users(

    limit: Optional[int] = Query(100, ge=1, le=500),

    offset: int = Query(0, ge=0),

    cursor: Optional[str] = Query(None),

    db: Session = Depends(get_db),

    current_admin: dict = Depends(get_current_admin),

):

    require_permission("users.read", current_admin)

    return get_all_users(db, limit=limit, offset=offset, cursor=cursor)





@router.put("/users/{user_id}/role")

def set_user_role(

    user_id: int,

    role: str,

    db: Session = Depends(get_db),

    current_admin: dict = Depends(require_admin_2fa_verified),

):

    """Update a user's role. Requires 2FA verification."""

    require_permission("users.role.update", current_admin)

    return publish_gov_update_user_role_requested(user_id, role, current_admin, db)





@router.post("/users/{user_id}/toggle-active")

def toggle_user_status(

    user_id: int,

    db: Session = Depends(get_db),

    current_admin: dict = Depends(require_admin_2fa_verified),

):

    """Enable or disable a user account. Requires 2FA verification."""

    require_permission("users.toggle_active", current_admin)

    return publish_gov_toggle_user_active_requested(user_id, current_admin, db)







@router.delete("/users/bulk")

def bulk_delete_users(

    body: BulkDeleteUsersBody,

    db: Session = Depends(get_db),

    current_admin: dict = Depends(require_admin_2fa_verified),

):

    """Bulk hard-delete multiple users (admin only). Requires 2FA verification."""

    require_permission("users.delete", current_admin)

    return publish_gov_bulk_delete_users_admin_requested(body.user_ids, current_admin, db)







@router.post("/users/bulk-toggle-active")

def bulk_toggle_users_active_route(

    body: BulkToggleActiveBody,

    db: Session = Depends(get_db),

    current_admin: dict = Depends(require_admin_2fa_verified),

):

    """Bulk enable or disable multiple user accounts. Requires 2FA verification."""

    require_permission("users.toggle_active", current_admin)

    return publish_gov_bulk_toggle_users_active_requested(body.user_ids, body.is_active, current_admin, db)







@router.post("/users/bulk-role")

def bulk_update_users_role_route(

    body: BulkUserRoleBody,

    db: Session = Depends(get_db),

    current_admin: dict = Depends(require_admin_2fa_verified),

):

    """Bulk update user roles for up to 200 users. Requires 2FA verification."""

    require_permission("users.role.update", current_admin)

    return publish_gov_bulk_update_users_role_requested(body.user_ids, body.role, current_admin, db)





@router.delete("/users/{user_id}")

def delete_user(

    user_id: int,

    delete_orders: bool = Query(False),

    db: Session = Depends(get_db),

    current_admin: dict = Depends(get_current_admin),

):

    """Hard-delete a single user (admin only). Blocked if user has orders."""

    require_permission("users.delete", current_admin)

    return delete_user_admin(user_id, current_admin, db, delete_orders=delete_orders)







@router.post("/users/{user_id}/reset-password")

def admin_reset_password(

    user_id: int,

    body: ResetPasswordBody,

    db: Session = Depends(get_db),

    current_admin: dict = Depends(require_admin_2fa_verified),

):

    """Admin: force-set any user's password without knowing the current one. Requires 2FA verification."""

    require_permission("users.reset_password", current_admin)

    return publish_gov_force_reset_password_admin_requested(user_id, body.new_password, current_admin, db)





# ── Staff Accounts ─────────────────────────────────────────────────────────────
