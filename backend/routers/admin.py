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

from utils.constants import MAX_BULK_ITEMS

from db.database import get_db
from db.schemas import (
    User as UserSchema,
    Product as ProductSchema,
    Order as OrderSchema,
    CouponSchema,
    ListPage,
    AuditLogSchema,
    AuditLogPage,
    CreateStaffAccount,
    UpdateStaffAccount,
    BulkUpdateStaffBody,
)
from controllers.admin_controller import (
    get_current_admin,
    get_current_user,
    require_admin,
    require_admin_2fa_enabled,
    require_admin_2fa_verified,
    require_permission,
    get_all_users,
    update_user_role,
    toggle_user_active,
    delete_user_admin,
    bulk_delete_users_admin,
    force_reset_password_admin,
    create_staff_account,
    update_staff_account,
    bulk_update_staff_accounts,
    delete_staff_account,
    get_all_orders,
    delete_order_admin,
    update_order_status,
    refund_order,
    update_order_tracking,
    get_all_products,
    delete_product_admin,
    restore_product_admin,
    get_analytics,
    get_supplier_comparison,
    get_customer_insights,
    get_audit_log_page,
    get_available_audit_actions,
    get_pending_suppliers,
    verify_supplier,
    reject_supplier,
    get_pending_products,
    approve_product,
    reject_product,
    toggle_product_badge,
    list_coupons,
    create_coupon,
    update_coupon,
    delete_coupon,
    list_tickets,
    get_ticket_detail,
    reply_to_ticket,
    update_ticket_status,
    list_pending_payouts,
    verify_payout,
    get_hierarchy_permissions,
    update_role_permissions,
    get_analytics_timeseries,
    get_top_products_analytics,
    get_user_growth_analytics,
    get_chatbot_analytics,
    get_all_suppliers,
    bulk_update_order_status_admin,
    bulk_delete_orders_admin,
    bulk_delete_products_admin,
    bulk_product_moderation,
    bulk_supplier_verification,
    bulk_manage_suppliers,
    bulk_update_users_role,
    bulk_toggle_users_active,
    list_staff_accounts,
    get_staff_permission_catalog,
    update_staff_account,
    list_pending_bank_accounts,
    delete_bank_account_record,
    verify_bank_account,
    get_database_overview,
)
from services.hierarchy_service import (
    get_authority_level,
    get_user_chain,
    get_all_subordinates,
    get_team_members,
    is_in_chain,
    can_manage as hierarchy_can_manage_service,
    get_org_chart,
    get_home_org_unit,
    reassign_manager,
    backfill_authority_levels,
)
from services.approval_matrix_service import (
    APPROVAL_RULES,
    can_approve,
    require_approval,
    resolve_approvers,
    get_approval_chain,
)
from controllers.banner_controller import (
    get_banners,
    get_banner_by_id,
    create_banner,
    update_banner,
    delete_banner,
    BannerCreate,
    BannerUpdate,
)
from controllers.export_controller import (
    export_users_csv,
    export_orders_csv,
    export_products_csv,
    export_coupons_csv,
    export_audit_logs_csv,
    export_transfer_csv,
    queue_export_job,
    download_export_job_result,
)
from controllers.promotion_controller import (
    get_promotion_config,
    update_promotion_config,
    list_promotion_tiers,
    create_promotion_tier,
    update_promotion_tier,
    delete_promotion_tier,
    preview_order_tier_discount,
)
from controllers import disputes_controller
from utils.backup import get_backup_manager
from services.misc_write_service import reset_demo_data as reset_demo_data_db

router = APIRouter()


# ── Users ──────────────────────────────────────────────────────────────────────

@router.get("/users", response_model=ListPage[dict])
def list_users(
    limit: Optional[int] = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    require_permission("users.read", current_admin)
    return get_all_users(db, limit=limit, offset=offset)

@router.put("/users/{user_id}/role")
def set_user_role(
    user_id: int,
    role: str,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin_2fa_verified),
):
    """Update a user's role. Requires 2FA verification."""
    require_permission("users.role.update", current_admin)
    return update_user_role(user_id, role, current_admin, db)

@router.post("/users/{user_id}/toggle-active")
def toggle_user_status(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin_2fa_verified),
):
    """Enable or disable a user account. Requires 2FA verification."""
    require_permission("users.toggle_active", current_admin)
    return toggle_user_active(user_id, current_admin, db)


class BulkDeleteUsersBody(BaseModel):
    user_ids: List[int]

    @field_validator("user_ids")
    @classmethod
    def limit_bulk_size(cls, v: List[int]) -> List[int]:
        if len(v) > MAX_BULK_ITEMS:
            raise ValueError(f"Cannot process more than {MAX_BULK_ITEMS} items at once")
        return v

@router.delete("/users/bulk")
def bulk_delete_users(
    body: BulkDeleteUsersBody,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin_2fa_verified),
):
    """Bulk hard-delete multiple users (admin only). Requires 2FA verification."""
    require_permission("users.delete", current_admin)
    return bulk_delete_users_admin(body.user_ids, current_admin, db)


class BulkToggleActiveBody(BaseModel):
    user_ids: List[int]
    is_active: bool

    @field_validator("user_ids")
    @classmethod
    def limit_bulk_size(cls, v: List[int]) -> List[int]:
        if len(v) > MAX_BULK_ITEMS:
            raise ValueError(f"Cannot process more than {MAX_BULK_ITEMS} items at once")
        return v

@router.post("/users/bulk-toggle-active")
def bulk_toggle_users_active_route(
    body: BulkToggleActiveBody,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin_2fa_verified),
):
    """Bulk enable or disable multiple user accounts. Requires 2FA verification."""
    require_permission("users.toggle_active", current_admin)
    return bulk_toggle_users_active(body.user_ids, body.is_active, current_admin, db)


class BulkUserRoleBody(BaseModel):
    user_ids: List[int]
    role: str

    @field_validator("user_ids")
    @classmethod
    def limit_bulk_size(cls, v: List[int]) -> List[int]:
        if len(v) > MAX_BULK_ITEMS:
            raise ValueError(f"Cannot process more than {MAX_BULK_ITEMS} items at once")
        return v

@router.post("/users/bulk-role")
def bulk_update_users_role_route(
    body: BulkUserRoleBody,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin_2fa_verified),
):
    """Bulk update user roles for up to 200 users. Requires 2FA verification."""
    require_permission("users.role.update", current_admin)
    return bulk_update_users_role(body.user_ids, body.role, current_admin, db)

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


class ResetPasswordBody(BaseModel):
    new_password: str

@router.post("/users/{user_id}/reset-password")
def admin_reset_password(
    user_id: int,
    body: ResetPasswordBody,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin_2fa_verified),
):
    """Admin: force-set any user's password without knowing the current one. Requires 2FA verification."""
    require_permission("users.reset_password", current_admin)
    return force_reset_password_admin(user_id, body.new_password, current_admin, db)


# ── Staff Accounts ─────────────────────────────────────────────────────────────
@router.post("/staff", status_code=201)
def create_staff(
    payload: CreateStaffAccount,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin_2fa_verified),
):
    """Admin-only: create a new staff account (admin/sub_admin/moderator/support). Requires 2FA verification."""
    require_permission("staff.create", current_admin)
    return create_staff_account(payload, current_admin, db)


@router.get("/staff")
def list_staff(
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),
):
    """Admin-only: list staff accounts with assignments and effective permissions."""
    require_permission("staff.view", current_admin)
    return list_staff_accounts(db)


@router.get("/staff/permission-catalog")
def staff_permission_catalog(
    current_admin: dict = Depends(require_admin),
):
    """Admin-only: fetch assignable staff permissions grouped for UI rendering."""
    require_permission("staff.manage", current_admin)
    return get_staff_permission_catalog()

@router.put("/staff/bulk")
def bulk_update_staff(
    body: BulkUpdateStaffBody,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin_2fa_verified),
):
    """Admin-only: bulk update multiple staff accounts with the same changes. Requires 2FA verification."""
    require_permission("staff.manage", current_admin)
    return bulk_update_staff_accounts(body.user_ids, body.updates, current_admin, db)

@router.put("/staff/{user_id}")
def update_staff(
    user_id: int,
    payload: UpdateStaffAccount,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin_2fa_verified),
):
    """Admin-only: update staff role, permissions, assignments, and profile metadata. Requires 2FA verification."""
    require_permission("staff.manage", current_admin)
    return update_staff_account(user_id, payload, current_admin, db)

@router.delete("/staff/{user_id}")
def delete_staff(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin_2fa_verified),
):
    """Admin-only: hard-delete a staff account when no retention blockers exist. Requires 2FA verification."""
    require_permission("staff.delete", current_admin)
    return delete_staff_account(user_id, current_admin, db)


# ── Orders ─────────────────────────────────────────────────────────────────────

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


class BulkOrderStatusBody(BaseModel):
    order_ids: List[int]
    status: str

    @field_validator("order_ids")
    @classmethod
    def limit_bulk_size(cls, v: List[int]) -> List[int]:
        if len(v) > MAX_BULK_ITEMS:
            raise ValueError(f"Cannot process more than {MAX_BULK_ITEMS} items at once")
        return v

@router.post("/orders/bulk-status")
def bulk_update_orders_status(
    body: BulkOrderStatusBody,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """Bulk-update order status for up to 200 orders."""
    require_permission("orders.manage", current_admin)
    return bulk_update_order_status_admin(body.order_ids, body.status, current_admin, db)


class BulkOrderDeleteBody(BaseModel):
    order_ids: List[int]

    @field_validator("order_ids")
    @classmethod
    def limit_bulk_size(cls, v: List[int]) -> List[int]:
        if len(v) > MAX_BULK_ITEMS:
            raise ValueError(f"Cannot process more than {MAX_BULK_ITEMS} items at once")
        return v

@router.delete("/orders/bulk")
def bulk_delete_orders(
    body: BulkOrderDeleteBody,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin_2fa_verified),
):
    """Bulk hard-delete orders (admin only, up to 100). Requires 2FA verification."""
    require_permission("orders.manage", current_admin)
    return bulk_delete_orders_admin(body.order_ids, current_admin, db)

@router.delete("/orders/{order_id}")
def delete_order_route(
    order_id: int,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin_2fa_verified),
):
    """Delete a single order. Requires 2FA verification."""
    require_permission("orders.manage", current_admin)
    return delete_order_admin(order_id, current_admin, db)

@router.put("/orders/{order_id}/status")
def set_order_status(
    order_id: int,
    status: str,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    require_permission("orders.manage", current_admin)
    return update_order_status(order_id, status, current_admin, db)

@router.post("/orders/{order_id}/refund")
def refund_order_route(
    order_id: int,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin_2fa_verified),
):
    """Process a refund for an order. Requires 2FA verification."""
    require_permission("orders.manage", current_admin)
    return refund_order(order_id, current_admin, db)

@router.put("/orders/{order_id}/tracking")
def set_order_tracking(
    order_id: int,
    tracking_number: str,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    require_permission("orders.manage", current_admin)
    return update_order_tracking(order_id, tracking_number, current_admin, db)


# ── Products ───────────────────────────────────────────────────────────────────

@router.get("/products", response_model=ListPage[ProductSchema])
def list_products(
    limit: Optional[int] = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    search: Optional[str] = Query(None),
    filter_value: Optional[str] = Query(None, alias="filter"),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    require_permission("products.manage", current_admin)
    return get_all_products(db, limit=limit, offset=offset, search=search, filter_value=filter_value)


class BulkProductDeleteBody(BaseModel):
    product_ids: List[int]

    @field_validator("product_ids")
    @classmethod
    def limit_bulk_size(cls, v: List[int]) -> List[int]:
        if len(v) > MAX_BULK_ITEMS:
            raise ValueError(f"Cannot process more than {MAX_BULK_ITEMS} items at once")
        return v

@router.delete("/products/bulk")
def bulk_delete_products(
    body: BulkProductDeleteBody,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """Bulk soft-delete products (up to 200)."""
    require_permission("products.manage", current_admin)
    return bulk_delete_products_admin(body.product_ids, current_admin, db)

@router.delete("/products/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    require_permission("products.manage", current_admin)
    return delete_product_admin(product_id, current_admin, db)


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

@router.post("/products/bulk-moderate")
def bulk_moderate_products(
    body: BulkProductModerationBody,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """Bulk approve or reject products pending moderation."""
    require_permission("moderation.products", current_admin)
    return bulk_product_moderation(body.product_ids, body.action, body.note, current_admin, db)


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

@router.post("/suppliers/bulk-verify")
def bulk_verify_suppliers(
    body: BulkSupplierVerifyBody,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """Bulk verify or reject supplier accounts."""
    require_permission("moderation.suppliers", current_admin)
    return bulk_supplier_verification(body.supplier_ids, body.action, body.note, current_admin, db)


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

@router.post("/suppliers/v1/bulk")
def bulk_manage_supplier_lifecycle(
    body: BulkSupplierLifecycleBody,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """Bulk supplier lifecycle actions: verify/reject/activate/suspend/delete."""
    require_permission("moderation.suppliers", current_admin)
    return bulk_manage_suppliers(body.supplier_ids, body.action, body.note, current_admin, db, badge_level=body.badge_level)

@router.post("/products/{product_id}/restore")
def restore_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),
):
    """Restore a soft-deleted product (admin only)."""
    require_permission("products.manage", current_admin)
    return restore_product_admin(product_id, current_admin, db)


# ── Analytics ──────────────────────────────────────────────────────────────────

@router.get("/analytics")
def analytics(
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    require_permission("analytics.view", current_admin)
    return get_analytics(db)


@router.get("/{country_code}/dashboard")
def admin_country_dashboard(
    country_code: str,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """Country-scoped admin dashboard stats.

    Returns summary numbers for the given country (or global if country is
    unknown) so the admin UI can render the top-row stat cards.
    """
    require_permission("analytics.view", current_admin)
    from utils.analytics_service import get_country_dashboard_stats
    return get_country_dashboard_stats(db, country_code=country_code.upper())


# ── Supplier Comparison ────────────────────────────────────────────────────────

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

@router.get("/customers/insights")
def customer_insights(
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """Top customers, popular categories, growth metrics."""
    require_permission("analytics.view", current_admin)
    return get_customer_insights(db)


# ── Audit Logs ─────────────────────────────────────────────────────────────────

# ── Supplier Verification Queue ───────────────────────────────────────────────

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
    return verify_supplier(user_id, note, current_admin, db)

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
    return reject_supplier(user_id, note, current_admin, db)

@router.put("/suppliers/{user_id}/badge")
def set_supplier_badge(
    user_id: int,
    badge_level: str,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """Admin: manually set a supplier's credibility badge level."""
    require_permission("moderation.suppliers", current_admin)
    import controllers.supplier_controller as _sc
    return _sc.admin_set_supplier_badge(user_id, badge_level, current_admin, db)

@router.post("/suppliers/{user_id}/refresh-badge")
def refresh_supplier_badge(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """Admin: recompute a supplier's credibility score and auto-assign badge."""
    require_permission("moderation.suppliers", current_admin)
    import controllers.supplier_controller as _sc
    return _sc.refresh_supplier_badge(user_id, db)


@router.get("/audit-logs", response_model=AuditLogPage)
def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    action: Optional[str] = Query(None),
    user_id: Optional[int] = Query(None),
    resource_type: Optional[str] = Query(None),
    resource_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """Paginated, filterable audit log viewer."""
    require_permission("audit.read", current_admin)
    return get_audit_log_page(
        db=db,
        page=page,
        page_size=page_size,
        action_filter=action,
        user_id_filter=user_id,
        resource_type_filter=resource_type,
        resource_id_filter=resource_id,
        status_filter=status,
        start_date=start_date,
        end_date=end_date,
        search=search,
    )


@router.get("/audit-logs/actions")
def audit_log_actions(
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """Distinct action types for filter dropdown."""
    require_permission("audit.read", current_admin)
    return get_available_audit_actions(db)


# ── Product Moderation ─────────────────────────────────────────────────────────

@router.get("/products/pending", response_model=ListPage[dict])
def list_pending_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(200, ge=1, le=500),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """Products awaiting admin approval."""
    require_permission("moderation.products", current_admin)
    return get_pending_products(db, limit=page_size, offset=(page - 1) * page_size)

@router.patch("/products/{product_id}/badge")
def set_product_badge(
    product_id: int,
    field: str = Query(..., description="is_hot | is_featured | is_new"),
    value: bool = Query(...),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """Admin: pin/unpin HOT, FEATURED or NEW badge on a product."""
    require_permission("products.manage", current_admin)
    return toggle_product_badge(product_id, field, value, current_admin, db)

@router.post("/products/{product_id}/approve")
def approve_product_route(
    product_id: int,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    require_permission("moderation.products", current_admin)
    require_approval(db, current_admin["id"], "product")
    return approve_product(product_id, current_admin, db)

@router.post("/products/{product_id}/reject")
def reject_product_route(
    product_id: int,
    note: Optional[str] = Body(None),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    require_permission("moderation.products", current_admin)
    require_approval(db, current_admin["id"], "product")
    return reject_product(product_id, note, current_admin, db)


# ── Coupon Management ──────────────────────────────────────────────────────────

@router.get("/coupons", response_model=ListPage[CouponSchema])
def list_all_coupons(
    skip: int = 0,
    limit: int | None = None,
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    require_permission("coupons.manage", current_admin)
    return list_coupons(db, skip=max(0, skip), limit=limit, search=search)

@router.post("/coupons", status_code=201)
def create_coupon_route(
    data: dict,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    require_permission("coupons.manage", current_admin)
    return create_coupon(data, current_admin, db)

@router.put("/coupons/{coupon_id}")
def update_coupon_route(
    coupon_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    require_permission("coupons.manage", current_admin)
    return update_coupon(coupon_id, data, current_admin, db)

@router.delete("/coupons/{coupon_id}")
def delete_coupon_route(
    coupon_id: int,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),
):
    require_permission("coupons.manage", current_admin)
    return delete_coupon(coupon_id, current_admin, db)


# ── Promotion Builder ─────────────────────────────────────────────────────────

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


@router.get("/promotions/config")
def get_promotion_config_route(
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    require_permission("coupons.manage", current_admin)
    return get_promotion_config(db)

@router.put("/promotions/config")
def update_promotion_config_route(
    body: PromotionConfigBody,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    require_permission("coupons.manage", current_admin)
    payload = {k: v for k, v in body.model_dump().items() if v is not None}
    return update_promotion_config(payload, current_admin, db)


@router.get("/promotions/tiers")
def list_promotion_tiers_route(
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    require_permission("coupons.manage", current_admin)
    return list_promotion_tiers(db)

@router.post("/promotions/tiers", status_code=201)
def create_promotion_tier_route(
    body: PromotionTierBody,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    require_permission("coupons.manage", current_admin)
    return create_promotion_tier(body.model_dump(), current_admin, db)

@router.put("/promotions/tiers/{tier_id}")
def update_promotion_tier_route(
    tier_id: int,
    body: PromotionTierUpdateBody,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    require_permission("coupons.manage", current_admin)
    payload = {k: v for k, v in body.model_dump().items() if v is not None}
    return update_promotion_tier(tier_id, payload, current_admin, db)

@router.delete("/promotions/tiers/{tier_id}")
def delete_promotion_tier_route(
    tier_id: int,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),
):
    require_permission("coupons.manage", current_admin)
    return delete_promotion_tier(tier_id, current_admin, db)

@router.post("/promotions/preview")
def preview_promotion_route(
    body: PromotionPreviewBody,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    require_permission("coupons.manage", current_admin)
    return preview_order_tier_discount(body.order_subtotal, body.coupon_discount, db)


# ── Support Tickets ────────────────────────────────────────────────────────────

@router.get("/tickets", response_model=ListPage[dict])
def list_all_tickets(
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(200, ge=1, le=500),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    require_permission("tickets.manage", current_admin)
    return list_tickets(db, status=status, limit=page_size, offset=(page - 1) * page_size)


@router.get("/tickets/{ticket_id}")
def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    require_permission("tickets.manage", current_admin)
    return get_ticket_detail(ticket_id, db)

@router.post("/tickets/{ticket_id}/reply")
def reply_ticket(
    ticket_id: int,
    body: dict,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    require_permission("tickets.manage", current_admin)
    return reply_to_ticket(ticket_id, body.get("message", ""), current_admin, db)

@router.put("/tickets/{ticket_id}/status")
def set_ticket_status(
    ticket_id: int,
    status: Optional[str] = Query(None),
    body: dict | None = Body(None),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    require_permission("tickets.manage", current_admin)
    resolved_status = str(status or (body or {}).get("status") or "").strip().lower()
    if not resolved_status:
        raise HTTPException(status_code=422, detail="status is required")
    return update_ticket_status(ticket_id, resolved_status, current_admin, db)


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


@router.get("/disputes", response_model=ListPage[dict])
def list_admin_disputes(
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    supplier_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    require_permission("moderation.suppliers", current_admin)
    return disputes_controller.list_admin_disputes(
        db=db,
        status=status,
        priority=priority,
        supplier_id=supplier_id,
        limit=page_size,
        offset=(page - 1) * page_size,
    )


@router.get("/disputes/{dispute_id}")
def get_admin_dispute(
    dispute_id: int,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    require_permission("moderation.suppliers", current_admin)
    return disputes_controller.get_admin_dispute(dispute_id, db)

@router.patch("/disputes/{dispute_id}")
def patch_admin_dispute(
    dispute_id: int,
    payload: dict = Body(default_factory=dict),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    require_permission("moderation.suppliers", current_admin)
    return disputes_controller.update_admin_dispute(dispute_id, payload, current_admin, db)

@router.post("/disputes/bulk")
def bulk_admin_dispute_action(
    body: AdminDisputeBulkActionBody,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    require_permission("moderation.suppliers", current_admin)
    return disputes_controller.bulk_update_admin_disputes(
        dispute_ids=body.dispute_ids,
        action=body.action,
        value=body.value,
        current_admin=current_admin,
        db=db,
    )


# ── Flash Sales ────────────────────────────────────────────────────────────────

from db.schemas import FlashSaleCreate, FlashSaleOut
from controllers.flash_sale_controller import (
    get_all_flash_sales,
    create_flash_sale,
    update_flash_sale,
    delete_flash_sale,
)


@router.get("/flash-sales", response_model=ListPage[FlashSaleOut])
def list_flash_sales(
    limit: Optional[int] = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """List all flash sales (admin)."""
    require_permission("coupons.manage", current_admin)
    return get_all_flash_sales(db, limit=limit, offset=offset, search=search)

@router.post("/flash-sales", response_model=FlashSaleOut, status_code=201)
def create_flash_sale_route(
    body: FlashSaleCreate,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),
):
    """Create a new flash sale."""
    require_permission("coupons.manage", current_admin)
    return create_flash_sale(body, current_admin, db)

@router.put("/flash-sales/{sale_id}", response_model=FlashSaleOut)
def update_flash_sale_route(
    sale_id: int,
    body: FlashSaleCreate,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),
):
    """Update an existing flash sale."""
    require_permission("coupons.manage", current_admin)
    return update_flash_sale(sale_id, body, current_admin, db)

@router.delete("/flash-sales/{sale_id}")
def delete_flash_sale_route(
    sale_id: int,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),
):
    """Delete a flash sale."""
    require_permission("coupons.manage", current_admin)
    return delete_flash_sale(sale_id, current_admin, db)


@router.get("/hierarchy/permissions")
def get_hierarchy_permissions_route(
    current_admin: dict = Depends(get_current_admin),
):
    require_permission("hierarchy.view", current_admin)
    return get_hierarchy_permissions(current_admin)


class UpdateRolePermissionsIn(BaseModel):
    permissions: List[str]

@router.put("/hierarchy/permissions/{role}")
def update_role_permissions_route(
    role: str,
    body: UpdateRolePermissionsIn,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin_2fa_verified),
):
    """Replace the full permission set for *role*. Admin-only. Requires 2FA verification."""
    return update_role_permissions(role, body.permissions, db, current_admin)


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


class ReassignManagerBody(BaseModel):
    user_id: int
    new_manager_id: int | None = None


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


class ResourceApprovalCheckIn(BaseModel):
    resource_type: str
    amount: Optional[float] = None


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


@router.get("/payouts/pending")
def get_pending_payouts_route(
    limit: int = 200,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    require_permission("payouts.verify", current_admin)
    return list_pending_payouts(db, limit=limit, offset=offset)

@router.post("/payouts/{payout_id}/verify")
def verify_payout_route(
    payout_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin_2fa_verified),
):
    require_permission("payouts.verify", current_admin)
    from models import Payout
    payout = db.query(Payout).filter(Payout.id == payout_id).first()
    amount = float(payout.amount) if payout and payout.amount is not None else None
    require_approval(db, current_admin["id"], "payout", amount=amount)
    return verify_payout(payout_id, data, current_admin, db)


# ── Email Marketing Stats (Admin) ──────────────────────────────────────────────

@router.get("/email/stats")
def admin_email_stats(
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """Real email marketing statistics from the database."""
    require_permission("analytics.view", current_admin)
    from sqlalchemy import func as sqlfunc, case as sql_case
    from models import NewsletterSubscriber, EmailCampaign, CampaignRecipient

    total_subscribers = db.query(sqlfunc.count(NewsletterSubscriber.id)).filter(
        NewsletterSubscriber.is_active == True
    ).scalar() or 0

    campaign_stats = db.query(
        sqlfunc.count(EmailCampaign.id).label("total"),
        sqlfunc.sum(sql_case((EmailCampaign.status == "sending", 1), else_=0)).label("active"),
    ).first()

    total_sent = db.query(sqlfunc.count(CampaignRecipient.id)).filter(
        CampaignRecipient.sent_at.isnot(None)
    ).scalar() or 0
    total_opened = db.query(sqlfunc.count(CampaignRecipient.id)).filter(
        CampaignRecipient.opened_at.isnot(None)
    ).scalar() or 0
    total_clicked = db.query(sqlfunc.count(CampaignRecipient.id)).filter(
        CampaignRecipient.clicked_at.isnot(None)
    ).scalar() or 0

    open_rate = round((total_opened / total_sent * 100), 1) if total_sent else 0
    click_rate = round((total_clicked / total_opened * 100), 1) if total_opened else 0

    recent_campaigns = db.query(EmailCampaign).order_by(
        EmailCampaign.created_at.desc()
    ).limit(10).all()

    def _ser_campaign(c: EmailCampaign):
        recipient_count = db.query(sqlfunc.count(CampaignRecipient.id)).filter(
            CampaignRecipient.campaign_id == c.id
        ).scalar() or 0
        return {
            "id": c.id,
            "name": c.name,
            "subject": c.subject,
            "status": c.status,
            "recipient_count": recipient_count,
            "sent_count": recipient_count,
            "opened_count": total_opened,
            "clicked_count": total_clicked,
            "send_at": c.send_at.isoformat() if c.send_at else None,
            "sent_at": c.send_at.isoformat() if c.send_at else None,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }

    return {
        "total_subscribers": total_subscribers,
        "active_campaigns": int(campaign_stats.active or 0),
        "total_campaigns": int(campaign_stats.total or 0),
        "total_sent": total_sent,
        "open_rate": open_rate,
        "click_rate": click_rate,
        "recent_campaigns": [_ser_campaign(c) for c in recent_campaigns],
    }


# ── Admin Logistics Overview ───────────────────────────────────────────────────

@router.get("/logistics/overview")
def admin_logistics_overview(
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """Admin overview of all shipments, carriers, and distribution channels."""
    require_permission("orders.manage", current_admin)
    from sqlalchemy import func as sqlfunc
    from models import Shipment, ShippingCarrier, ShippingZone

    shipment_counts = db.query(
        Shipment.status,
        sqlfunc.count(Shipment.id).label("count"),
    ).group_by(Shipment.status).all()

    channel_counts = db.query(
        Shipment.distribution_channel,
        sqlfunc.count(Shipment.id).label("count"),
    ).filter(Shipment.distribution_channel.isnot(None)).group_by(
        Shipment.distribution_channel
    ).all()

    carriers = db.query(ShippingCarrier).filter(ShippingCarrier.is_active == True).all()
    zones = db.query(ShippingZone).filter(ShippingZone.is_active == True).count()

    recent_shipments = db.query(Shipment).order_by(
        Shipment.updated_at.desc()
    ).limit(20).all()

    def _ser_shipment(s: Shipment):
        return {
            "id": s.id,
            "order_id": s.order_id,
            "supplier_id": s.supplier_id,
            "carrier_name": s.carrier_name,
            "tracking_number": s.tracking_number,
            "status": s.status,
            "distribution_channel": s.distribution_channel,
            "current_hub": s.current_hub,
            "scan_code": s.scan_code,
            "shipped_at": s.shipped_at.isoformat() if s.shipped_at else None,
            "estimated_delivery": s.estimated_delivery.isoformat() if s.estimated_delivery else None,
            "actual_delivery": s.actual_delivery.isoformat() if s.actual_delivery else None,
        }

    return {
        "shipment_by_status": {s: c for s, c in shipment_counts},
        "shipment_by_channel": {ch: c for ch, c in channel_counts},
        "active_carriers": [
            {"id": c.id, "name": c.name, "code": c.code, "is_global": c.supplier_id is None}
            for c in carriers
        ],
        "active_zones": zones,
        "recent_shipments": [_ser_shipment(s) for s in recent_shipments],
    }


# ── Admin Supplier Documents ────────────────────────────────────────────────────

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
    import controllers.supplier_document_controller as _sdc
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
    import controllers.supplier_document_controller as _sdc
    return _sdc.admin_review_document(doc_id, data, current_admin, db)


# ── Admin Invoices Overview ────────────────────────────────────────────────────

@router.get("/invoices/overview")
def admin_invoices_overview(
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """Admin overview of supply chain invoices."""
    require_permission("orders.manage", current_admin)
    import controllers.invoice_controller as _ic
    return _ic.get_invoice_overview(db)


# ── Admin Logistics Partners ───────────────────────────────────────────────────

@router.get("/logistics/partners")
def admin_logistics_partners(
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """Admin: list all logistics partners."""
    require_permission("orders.manage", current_admin)
    import controllers.logistics_partner_controller as _lpc
    return _lpc.list_partners(current_admin, db)

@router.post("/logistics/partners", status_code=201)
def admin_create_logistics_partner(
    data: dict,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),
):
    """Admin: onboard a new logistics partner."""
    import controllers.logistics_partner_controller as _lpc
    return _lpc.create_partner(data, current_admin, db)

@router.put("/logistics/partners/{partner_id}")
def admin_update_logistics_partner(
    partner_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """Admin: update logistics partner details."""
    require_permission("orders.manage", current_admin)
    import controllers.logistics_partner_controller as _lpc
    return _lpc.update_partner(partner_id, data, current_admin, db)


# -- Advanced Analytics ---------------------------------------------------------

@router.get("/analytics/timeseries")
def analytics_timeseries(
    period: str = Query("30d", pattern=r"^(7d|30d|90d|1y)$"),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """Revenue & order timeseries for chart rendering."""
    require_permission("analytics.view", current_admin)
    return get_analytics_timeseries(period, db)


@router.get("/analytics/top-products")
def analytics_top_products(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """Top-selling products by units sold."""
    require_permission("analytics.view", current_admin)
    return get_top_products_analytics(limit, db)


@router.get("/analytics/user-growth")
def analytics_user_growth(
    period: str = Query("30d", pattern=r"^(7d|30d|90d|1y)$"),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """Daily new user registrations."""
    require_permission("analytics.view", current_admin)
    return get_user_growth_analytics(period, db)


@router.get("/analytics/chatbot")
def analytics_chatbot(
    period: str = Query("30d", pattern=r"^(7d|30d|90d|1y)$"),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),
):
    """Chatbot demand, refinement, and click engagement analytics. Admin only."""
    return get_chatbot_analytics(period, db)


# -- All Suppliers --------------------------------------------------------------

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

@router.get("/banners", response_model=ListPage[dict])
def admin_list_banners(
    page: int = Query(1, ge=1),
    page_size: int = Query(200, ge=1, le=500),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),
):
    """Admin: list all banners (active and inactive)."""
    from controllers.banner_controller import get_banners_page
    return get_banners_page(db, active_only=False, limit=page_size, offset=(page - 1) * page_size)


@router.get("/banners/{banner_id:int}")
def admin_get_banner(
    banner_id: int,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),
):
    """Admin: get single banner by ID."""
    return get_banner_by_id(banner_id, db)

@router.post("/banners", status_code=201)
def admin_create_banner(
    payload: BannerCreate,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),
):
    """Admin: create a new banner."""
    return create_banner(payload, current_admin["id"], current_admin, db)

@router.put("/banners/{banner_id}")
def admin_update_banner(
    banner_id: int,
    payload: BannerUpdate,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),
):
    """Admin: update a banner."""
    return update_banner(banner_id, payload, current_admin, db)

@router.delete("/banners/{banner_id}")
def admin_delete_banner(
    banner_id: int,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),
):
    """Admin: delete a banner."""
    return delete_banner(banner_id, current_admin, db)


# ── Data Export ────────────────────────────────────────────────────────────────

@router.get("/export/users")
def admin_export_users(
    background: bool = Query(False),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """Admin: stream all users as a CSV download."""
    require_admin(current_admin)
    if background:
        return JSONResponse(status_code=202, content=queue_export_job("users", current_admin))
    return export_users_csv(current_admin, db)


@router.get("/export/orders")
def admin_export_orders(
    background: bool = Query(False),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """Admin: stream all orders as a CSV download."""
    require_admin(current_admin)
    if background:
        return JSONResponse(status_code=202, content=queue_export_job("orders", current_admin))
    return export_orders_csv(current_admin, db)


@router.get("/export/products")
def admin_export_products(
    background: bool = Query(False),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """Admin: stream all products as a CSV download."""
    require_admin(current_admin)
    if background:
        return JSONResponse(status_code=202, content=queue_export_job("products", current_admin))
    return export_products_csv(current_admin, db)


@router.get("/export/coupons")
def admin_export_coupons(
    background: bool = Query(False),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """Admin: stream all coupons as a CSV download."""
    require_admin(current_admin)
    if background:
        return JSONResponse(status_code=202, content=queue_export_job("coupons", current_admin))
    return export_coupons_csv(current_admin, db)


@router.get("/export/audit-logs")
def admin_export_audit_logs(
    days: int = Query(30, ge=1, le=365),
    background: bool = Query(False),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """Admin: stream audit logs as a CSV download (default last 30 days)."""
    require_admin(current_admin)
    if background:
        return JSONResponse(status_code=202, content=queue_export_job("audit-logs", current_admin, days=days))
    return export_audit_logs_csv(current_admin, db, days=days)


@router.get("/export/supplier-payout-transfers")
def admin_export_supplier_payout_transfers(
    background: bool = Query(False),
    provider: str = Query("manual_csv"),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """Admin: export supplier payout transfer instructions for bank execution."""
    require_admin(current_admin)
    if background:
        return JSONResponse(
            status_code=202,
            content=queue_export_job("supplier-payout-transfers", current_admin, provider=provider),
        )
    return export_transfer_csv("supplier-payout-transfers", current_admin, db, provider=provider)


@router.get("/export/logistics-payout-transfers")
def admin_export_logistics_payout_transfers(
    background: bool = Query(False),
    provider: str = Query("manual_csv"),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """Admin: export logistics payout transfer instructions for bank execution."""
    require_admin(current_admin)
    if background:
        return JSONResponse(
            status_code=202,
            content=queue_export_job("logistics-payout-transfers", current_admin, provider=provider),
        )
    return export_transfer_csv("logistics-payout-transfers", current_admin, db, provider=provider)


@router.get("/export/cod-remittance-transfers")
def admin_export_cod_remittance_transfers(
    background: bool = Query(False),
    provider: str = Query("manual_csv"),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """Admin: export COD remittance instructions with Zozi treasury bank details."""
    require_admin(current_admin)
    if background:
        return JSONResponse(
            status_code=202,
            content=queue_export_job("cod-remittance-transfers", current_admin, provider=provider),
        )
    return export_transfer_csv("cod-remittance-transfers", current_admin, db, provider=provider)


@router.get("/export/jobs/{job_id}/download")
def admin_download_export_job(
    job_id: str,
    current_admin: dict = Depends(get_current_admin),
):
    """Admin: download a completed background export artifact."""
    require_admin(current_admin)
    return download_export_job_result(job_id, current_admin)


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

    from utils.key_rotation import rotate_encryption_key
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
    return delete_bank_account_record(kind, account_id, current_admin, db)


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
    from services.legal_contract_service import LegalContractService
    
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
    from services.audit_trail_service import AuditTrailService
    
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

    return reset_demo_data_db(db)


