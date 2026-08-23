from domains.governance.events import publish_gov_delete_bank_account_record_requested
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

from domains.finance.services.payments.payout_approval_read_service import list_pending_payouts

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







@router.get("/database/overview")

def admin_database_overview(

    db: Session = Depends(get_db),

    current_admin: dict = Depends(get_current_admin),

):

    """Admin: inspect database health and schema inventory for operational handling."""

    require_admin(current_admin)

    return get_database_overview(db)





# ── Database Backup ────────────────────────────────────────────────────────────



@router.post("/backup/trigger", status_code=201)

def admin_trigger_backup(

    current_admin: dict = Depends(get_current_admin),

):

    """Admin: manually trigger an immediate database backup."""

    require_admin(current_admin)

    path = get_backup_manager().create_backup()

    if path is None:

        from fastapi import HTTPException

        raise HTTPException(status_code=500, detail="Backup failed — check server logs")

    return {"detail": "Backup created", "filename": path.name}







@router.get("/backup/list")

def admin_list_backups(

    current_admin: dict = Depends(get_current_admin),

):

    """Admin: list all available backup files."""

    require_admin(current_admin)

    return {"backups": get_backup_manager().list_backups()}







@router.get("/backup/download/{filename}")

def admin_download_backup(

    filename: str,

    current_admin: dict = Depends(get_current_admin),

):

    """Admin: download a specific backup file."""

    require_admin(current_admin)

    from fastapi import HTTPException

    from fastapi.responses import FileResponse

    try:

        path = get_backup_manager().get_backup_path(filename)

    except (ValueError, FileNotFoundError) as exc:

        status_code = 400 if isinstance(exc, ValueError) else 404

        raise HTTPException(status_code=status_code, detail=str(exc))

    return FileResponse(

        path=str(path),

        filename=filename,

        media_type="application/octet-stream",

    )





@router.post("/backup/restore-drill")

def admin_run_backup_restore_drill(

    filename: str | None = None,

    current_admin: dict = Depends(get_current_admin),

):

    """Admin: verify that the latest or named backup can be restored from local/cloud storage."""

    require_admin(current_admin)

    from fastapi import HTTPException



    try:

        return get_backup_manager().run_restore_drill(filename)

    except FileNotFoundError as exc:

        raise HTTPException(status_code=404, detail=str(exc))

    except ValueError as exc:

        raise HTTPException(status_code=400, detail=str(exc))

    except RuntimeError as exc:

        raise HTTPException(status_code=500, detail=str(exc))





# ── Security Key Rotation ──────────────────────────────────────────────────────



@router.post("/security/rotate-key")

def admin_rotate_encryption_key(

    payload: dict,

    current_admin: dict = Depends(get_current_admin),

    db: Session = Depends(get_db),

):

    """Superadmin: re-encrypt all EncryptedString fields with a new key.



    Body: ``{"old_key": "...", "new_key": "..."}``



    Both ``old_key`` and ``new_key`` are the raw (pre-derivation) key strings,

    exactly as you would set ``FIELD_ENCRYPTION_KEY`` in the environment.

    After a successful rotation you must update the env-var and restart the app.

    """

    from fastapi import HTTPException

    require_admin(current_admin)



    old_key = payload.get("old_key", "").strip()

    new_key = payload.get("new_key", "").strip()

    if not old_key or not new_key:

        raise HTTPException(status_code=422, detail="Both old_key and new_key are required")

    if old_key == new_key:

        raise HTTPException(status_code=422, detail="new_key must differ from old_key")



    from infrastructure.utils.key_rotation import rotate_encryption_key

    result = rotate_encryption_key(old_key, new_key, db)

    return result





# ── Admin: Recipient Bank Account Verification ─────────────────────────────────





@router.get("/bank-accounts/pending")

def admin_list_pending_bank_accounts(

    kind: str = Query(..., description="supplier or logistics_partner"),

    limit: int = 200,

    offset: int = 0,

    current_admin: dict = Depends(get_current_admin),

    db: Session = Depends(get_db),

):

    """List pending bank accounts for admin verification."""

    return list_pending_bank_accounts(kind, db, current_admin, limit=limit, offset=offset)





@router.post("/bank-accounts/{account_id}/approve")

def admin_approve_bank_account(

    account_id: int,

    kind: str = Query(..., description="supplier or logistics_partner"),

    body: Optional[dict] = None,

    current_admin: dict = Depends(get_current_admin),

    db: Session = Depends(get_db),

):

    """Approve a supplier or logistics partner bank account for use in payout exports."""

    note = (body or {}).get("note") if body else None

    return verify_bank_account(kind, account_id, "approve", note, current_admin, db)





@router.post("/bank-accounts/{account_id}/reject")

def admin_reject_bank_account(

    account_id: int,

    kind: str = Query(..., description="supplier or logistics_partner"),

    body: Optional[dict] = None,

    current_admin: dict = Depends(get_current_admin),

    db: Session = Depends(get_db),

):

    """Reject a supplier or logistics partner bank account."""

    note = (body or {}).get("note") if body else None

    return verify_bank_account(kind, account_id, "reject", note, current_admin, db)





@router.delete("/bank-accounts/{account_id}")

def admin_delete_bank_account(

    account_id: int,

    kind: str = Query(..., description="supplier or logistics_partner"),

    current_admin: dict = Depends(get_current_admin),

    db: Session = Depends(get_db),

):

    """Delete a supplier or logistics partner bank account record."""

    return publish_gov_delete_bank_account_record_requested(kind, account_id, current_admin, db)





# %% Public Config Endpoints %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%





@router.get("/config/checkout")

def get_checkout_config():

    """

    Public checkout configuration endpoint.

    Returns VAT rate, shipping flat rate, and free shipping threshold.

    """

    return {

        "vat_rate": 0.05,

        "shipping_flat_rate": 2.0,

        "free_shipping_threshold": 0.0,

    }





# ── Legal Contract Generation ─────────────────────────────────────────────────────





@router.post("/countries/{country_code}/legal-contracts/generate")

def generate_legal_contract(

    country_code: str = Path(...),

    payload: Optional[dict] = Body(None),

    db: Session = Depends(get_db),

    current_admin: dict = Depends(get_current_admin),

):

    """Generate a legal contract for a country."""

    require_permission("legal.contracts", current_admin)

    from domains.suppliers.services.legal_contract_service import LegalContractService

    

    if payload is None:

        payload = {}

    

    template_type = payload.get("template_type", "terms")

    variables = payload.get("variables", {})

    

    result = LegalContractService.generate_contract(country_code, template_type, variables, db)

    return result





# ── Audit Trail ─────────────────────────────────────────────────────────────────





@router.get("/countries/{country_code}/audit-trail")

def get_country_audit_trail(

    country_code: str = Path(...),

    table_name: Optional[str] = Query(None),

    record_id: Optional[int] = Query(None),

    limit: int = Query(100, ge=1, le=500),

    db: Session = Depends(get_db),

    current_admin: dict = Depends(get_current_admin),

):

    """Get audit trail for a country's financial changes."""

    require_permission("audit.read", current_admin)

    from domains.governance.services.audit.audit_trail_service import AuditTrailService

    

    return AuditTrailService.get_audit_trail(

        country_code,

        table_name=table_name,

        record_id=record_id,

        limit=limit

    )





# ── Data Reset (Demo / Dev) ────────────────────────────────────────────────────





@router.get("/reset", status_code=200)

def admin_reset_demo_data(

    db: Session = Depends(get_db),

    current_admin: dict = Depends(get_current_admin),

):

    """

    Clear all non-essential seed data — orders, products, reviews, communication

    data, coupons, and non-admin users — so the demo environment can be reset

    from the UI without SSH or terminal access.



    Admin user accounts (role=admin) are preserved.

    """

    require_admin(current_admin)



    app_env = getattr(settings, "APP_ENV", None)

    if not app_env or app_env not in ("development", "dev", "test"):

        raise HTTPException(

            status_code=400,

            detail="Reset is only available in development/test environments",

        )



    return reset_demo_data(db)
