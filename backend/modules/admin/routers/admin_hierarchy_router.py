from domains.governance.events import publish_gov_update_role_permissions_requested
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

from domains.accounts.services.admin_products_service import approve_product











from domains.accounts.services.admin_promotions_service import create_coupon



from domains.accounts.services.customer_coupons_create_service import delete_coupon




from domains.accounts.services.identity_admin_service import delete_user_admin


from domains.governance.services.orders_service import get_all_orders

from domains.governance.services.products_service import get_all_products

from domains.governance.services.suppliers_service import get_all_suppliers

from domains.governance.services.users_service import get_all_users

from domains.governance.services.analytics_service import get_analytics

from domains.governance.services.analytics_service import get_analytics_timeseries

from domains.governance.services.misc_service import get_audit_log_page

from domains.governance.services.misc_service import get_available_audit_actions

from domains.governance.services.analytics_service import get_chatbot_analytics



from domains.governance.services.analytics_service import get_customer_insights

from domains.governance.services.database_service import get_database_overview

from domains.governance.services.permissions_service import get_hierarchy_permissions

from domains.governance.services.products_service import get_pending_products

from domains.governance.services.suppliers_service import get_pending_suppliers

from domains.governance.services.permissions_service import get_staff_permission_catalog

from domains.governance.services.suppliers_service import get_supplier_comparison

from domains.governance.services.admin_controller import get_ticket_detail

from domains.governance.services.analytics_service import get_top_products_analytics

from domains.governance.services.analytics_service import get_user_growth_analytics

from domains.accounts.services.customer_coupons_create_service import list_coupons

from domains.governance.services.users_service import list_pending_bank_accounts

from domains.finance.services.payout_approval_read_service import list_pending_payouts

from domains.governance.services.users_service import list_staff_accounts

from domains.comms.services.tickets_service import list_tickets


from domains.accounts.services.admin_products_service import reject_product


from domains.comms.services.tickets_service import reply_to_ticket


from domains.governance.services.admin_controller import require_admin_2fa_verified

from domains.governance.services.effective_permissions import require_permission




from domains.orders.services.coupons_write_service import update_coupon





from domains.comms.services.tickets_write_service import update_ticket_status


from domains.accounts.services.payroll_service import verify_bank_account

from domains.accounts.services.logistics_partner_service import verify_payout


from domains.catalog.services.banner_controller import BannerCreate

from domains.catalog.services.banner_controller import BannerUpdate

from domains.catalog.services.banner_controller import create_banner

from domains.catalog.services.banner_controller import delete_banner

from domains.catalog.services.banner_controller import get_banner_by_id

from domains.catalog.services.banner_controller import update_banner

from domains.accounts.services.export_controller import (

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

from domains.accounts.services.approval_matrix_service import APPROVAL_RULES

from domains.accounts.services.approval_matrix_service import can_approve

from domains.accounts.services.approval_matrix_service import get_approval_chain

from domains.accounts.services.approval_matrix_service import require_approval

from domains.accounts.services.approval_matrix_service import resolve_approvers

from domains.accounts.services.hierarchy_service import backfill_authority_levels

from domains.accounts.services.hierarchy_service import get_all_subordinates

from domains.accounts.services.hierarchy_service import get_authority_level

from domains.accounts.services.hierarchy_service import get_org_chart

from domains.accounts.services.hierarchy_service import get_team_members

from domains.accounts.services.hierarchy_service import get_user_chain

from domains.accounts.services.hierarchy_service import is_in_chain

from domains.accounts.services.hierarchy_service import reassign_manager

from domains.accounts.services.hierarchy_service import can_manage as hierarchy_can_manage_service

from domains.comms.services.misc_write_service import reset_demo_data

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







@router.get("/hierarchy/permissions")

def get_hierarchy_permissions_route(

    current_admin: dict = Depends(get_current_admin),

):

    require_permission("hierarchy.view", current_admin)

    return get_hierarchy_permissions(current_admin)







@router.put("/hierarchy/permissions/{role}")

def update_role_permissions_route(

    role: str,

    body: UpdateRolePermissionsIn,

    db: Session = Depends(get_db),

    current_admin: dict = Depends(require_admin_2fa_verified),

):

    """Replace the full permission set for *role*. Admin-only. Requires 2FA verification."""

    return publish_gov_update_role_permissions_requested(role, body.permissions, db, current_admin)







@router.get("/hierarchy/authority-level")

def hierarchy_authority_level(

    user_id: int = Query(..., gt=0),

    db: Session = Depends(get_db),

    current_admin: dict = Depends(get_current_user),

):

    require_permission("hierarchy.view", current_admin)

    level = get_authority_level(db, user_id)

    return {"user_id": user_id, "authority_level": level}







@router.get("/hierarchy/chain/{user_id}")

def hierarchy_chain(

    user_id: int,

    db: Session = Depends(get_db),

    current_admin: dict = Depends(get_current_user),

):

    require_permission("hierarchy.view", current_admin)

    chain = get_user_chain(db, user_id)

    return {"user_id": user_id, "chain": chain}







@router.get("/hierarchy/subordinates/{user_id}")

def hierarchy_subordinates(

    user_id: int,

    db: Session = Depends(get_db),

    current_admin: dict = Depends(get_current_user),

):

    require_permission("hierarchy.view", current_admin)

    subordinates = get_all_subordinates(db, user_id)

    return {"user_id": user_id, "subordinates": subordinates}







@router.get("/hierarchy/can-manage")

def hierarchy_can_manage(

    manager_id: int = Query(..., gt=0),

    target_id: int = Query(..., gt=0),

    db: Session = Depends(get_db),

    current_admin: dict = Depends(get_current_user),

):

    require_permission("hierarchy.view", current_admin)

    result = hierarchy_can_manage_service(db, manager_id, target_id)

    return {"manager_id": manager_id, "target_id": target_id, "can_manage": result}







@router.get("/hierarchy/org-chart")

def hierarchy_org_chart(

    org_unit_id: Optional[int] = Query(None),

    db: Session = Depends(get_db),

    current_admin: dict = Depends(get_current_user),

):

    require_permission("hierarchy.view", current_admin)

    chart = get_org_chart(db, org_unit_id)

    return chart







@router.get("/hierarchy/team-members/{user_id}")

def hierarchy_team_members(

    user_id: int,

    db: Session = Depends(get_db),

    current_admin: dict = Depends(get_current_user),

):

    require_permission("hierarchy.view", current_admin)

    members = get_team_members(db, user_id)

    return {"user_id": user_id, "team_members": members}







@router.get("/hierarchy/in-chain")

def hierarchy_in_chain(

    upper_user_id: int = Query(..., gt=0),

    lower_user_id: int = Query(..., gt=0),

    db: Session = Depends(get_db),

    current_admin: dict = Depends(get_current_user),

):

    require_permission("hierarchy.view", current_admin)

    result = is_in_chain(db, upper_user_id, lower_user_id)

    return {"upper_user_id": upper_user_id, "lower_user_id": lower_user_id, "in_chain": result}







@router.post("/hierarchy/reassign-manager")

def hierarchy_reassign_manager(

    body: ReassignManagerBody,

    db: Session = Depends(get_db),

    current_admin: dict = Depends(require_admin),

):

    return reassign_manager(db, body.user_id, body.new_manager_id)







@router.post("/hierarchy/backfill-authority-levels")

def hierarchy_backfill_authority_levels(

    db: Session = Depends(get_db),

    current_admin: dict = Depends(require_admin),

):

    updated = backfill_authority_levels(db)

    return {"updated": updated}







@router.get("/hierarchy/approval-matrix/rules")

def get_approval_matrix_rules(

    current_admin: dict = Depends(get_current_user),

):

    require_permission("hierarchy.view", current_admin)

    return {

        resource_type: {

            "label": rule["label"],

            "min_authority_level": rule["min_authority_level"],

            "department": rule.get("department"),

            "org_unit_required": rule.get("org_unit_required", False),

            "description": rule["description"],

        }

        for resource_type, rule in APPROVAL_RULES.items()

    }







@router.post("/hierarchy/approval-matrix/check")

def check_approval_eligibility(

    body: ResourceApprovalCheckIn,

    user_id: int = Query(..., gt=0),

    db: Session = Depends(get_db),

    current_admin: dict = Depends(get_current_user),

):

    require_permission("hierarchy.view", current_admin)

    result = can_approve(db, user_id, body.resource_type, amount=body.amount)

    return result







@router.get("/hierarchy/approvers/{resource_type}")

def get_resource_approvers(

    resource_type: str,

    org_unit_id: Optional[int] = Query(None),

    db: Session = Depends(get_db),

    current_admin: dict = Depends(get_current_user),

):

    require_permission("hierarchy.view", current_admin)

    approvers = resolve_approvers(db, resource_type, org_unit_id=org_unit_id)

    return {

        "resource_type": resource_type,

        "org_unit_id": org_unit_id,

        "approvers": approvers,

        "count": len(approvers),

    }







@router.get("/hierarchy/approval-chain/{user_id}/{resource_type}")

def get_user_approval_chain(

    user_id: int,

    resource_type: str,

    db: Session = Depends(get_db),

    current_admin: dict = Depends(get_current_user),

):

    require_permission("hierarchy.view", current_admin)

    chain = get_approval_chain(db, user_id, resource_type)

    return {

        "user_id": user_id,

        "resource_type": resource_type,

        "chain": chain,

        "count": len(chain),

    }
