"""
Admin Router  route declarations only (HTTP layer).
All business logic lives in controllers/admin_controller.py.
"""
from typing import List, Optional
from fastapi import Body, Depends, HTTPException, Path, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session
from infrastructure.utils.constants import MAX_BULK_ITEMS
from infrastructure.database.database import get_db, Base
from infrastructure.database.schemas import User as UserSchema, Product as ProductSchema, Order as OrderSchema, CouponSchema, ListPage, AuditLogSchema, AuditLogPage, CreateStaffAccount, UpdateStaffAccount, BulkUpdateStaffBody
# TODO: Module not yet created
# from domains.governance.services.settings.admin_controller import get_current_admin
from domains.accounts.ports import get_current_user, get_hierarchy_permissions, get_staff_permission_catalog, update_role_permissions
from infrastructure.utils.dependencies import require_admin
# TODO: Module not yet created
# from domains.governance.services.settings.admin_controller import require_admin_2fa_enabled
# TODO: Module not yet created
# from domains.governance.services.settings.admin_controller import require_admin_2fa_verified
# TODO: Module not yet created
# from domains.governance.services.permissions.effective_permissions import require_permission
# TODO: Module not yet created
# from domains.governance.services.users.users_service_accounts import get_all_users
# TODO: Module not yet created
# from domains.governance.services.users.users_service_accounts import update_user_role
# TODO: Module not yet created
# from domains.governance.services.users.users_service_accounts import toggle_user_active
from domains.governance.ports import delete_user_admin
# TODO: Module not yet created
# from domains.governance.services.users.admin_users import bulk_delete_users_admin
# TODO: Module not yet created
# from domains.governance.services.users.admin_users import force_reset_password_admin
# TODO: Module not yet created
# from domains.governance.services.users.users_service_accounts import create_staff_account
# TODO: Module not yet created
# # TODO: Module not yet created
# from domains.governance.services.users.users_service_accounts import update_staff_account
# TODO: Module not yet created
# from domains.governance.services.users.users_service_accounts import bulk_update_staff_accounts
# TODO: Module not yet created
# from domains.governance.services.users.users_service_accounts import delete_staff_account
# TODO: Module not yet created
# from domains.governance.services.orders.orders_service import get_all_orders
# TODO: Module not yet created
# from domains.governance.services.orders.orders_service import delete_order_admin
# TODO: Module not yet created
# from domains.governance.services.orders.orders_service import update_order_status
# TODO: Module not yet created
# from domains.governance.services.orders.orders_service import refund_order
# TODO: Module not yet created
# from domains.governance.services.orders.orders_service import update_order_tracking
# TODO: Module not yet created
# from domains.governance.services.products.products_service import get_all_products
# TODO: Module not yet created
# from domains.governance.services.products.products_service import delete_product_admin
# TODO: Module not yet created
# from domains.governance.services.products.products_service import restore_product_admin
# TODO: Module not yet created
# from domains.governance.services.analytics.analytics_service import get_analytics
# TODO: Module not yet created
# from domains.governance.services.suppliers.suppliers_service import get_supplier_comparison
# TODO: Module not yet created
# from domains.governance.services.analytics.analytics_service import get_customer_insights
from domains.governance.ports import get_audit_log_page, get_available_audit_actions
# TODO: Module not yet created
# from domains.governance.services.suppliers.suppliers_service import get_pending_suppliers
# TODO: Module not yet created
# from domains.governance.services.suppliers.suppliers_service import verify_supplier
# TODO: Module not yet created
# from domains.governance.services.suppliers.suppliers_service import reject_supplier
# TODO: Module not yet created
# from domains.governance.services.products.products_service import get_pending_products
from domains.governance.ports import approve_product
from domains.governance.ports import reject_product
# TODO: Module not yet created
# from domains.governance.services.products.products_service import toggle_product_badge
from domains.governance.ports import list_coupons
from domains.governance.ports import create_coupon
from domains.orders.ports import update_coupon
from domains.governance.ports import delete_coupon
# TODO: Module not yet created
# from domains.comms.services.ticket.tickets_service import list_tickets
# TODO: Module not yet created
# from domains.governance.services.settings.admin_controller import get_ticket_detail
# TODO: Module not yet created
# from domains.comms.services.ticket.tickets_service import reply_to_ticket
# TODO: Module not yet created
# from domains.comms.services.ticket.tickets_write_service import update_ticket_status
from domains.finance.ports import list_pending_payouts
from domains.governance.ports import verify_payout
# TODO: Module not yet created
# # TODO: Module not yet created
# from domains.governance.services.analytics.analytics_service import get_analytics_timeseries
# TODO: Module not yet created
# from domains.governance.services.analytics.analytics_service import get_top_products_analytics
# TODO: Module not yet created
# from domains.governance.services.analytics.analytics_service import get_user_growth_analytics
# TODO: Module not yet created
# from domains.governance.services.analytics.analytics_service import get_chatbot_analytics
# TODO: Module not yet created
# from domains.governance.services.suppliers.suppliers_service import get_all_suppliers
# TODO: Module not yet created
# from domains.governance.services.orders.orders_service import bulk_update_order_status_admin
# TODO: Module not yet created
# from domains.governance.services.orders.orders_service import bulk_delete_orders_admin
# TODO: Module not yet created
# from domains.governance.services.products.products_service import bulk_delete_products_admin
# TODO: Module not yet created
# from domains.governance.services.products.products_service import bulk_product_moderation
# TODO: Module not yet created
# from domains.governance.services.suppliers.suppliers_service import bulk_supplier_verification
# TODO: Module not yet created
# from domains.governance.services.suppliers.suppliers_service import bulk_manage_suppliers
# TODO: Module not yet created
# from domains.governance.services.users.users_service_accounts import bulk_update_users_role
# TODO: Module not yet created
# from domains.governance.services.users.users_service_accounts import bulk_toggle_users_active
# TODO: Module not yet created
# from domains.governance.services.users.users_service_accounts import list_staff_accounts
# TODO: Module not yet created
# # TODO: Module not yet created
# from domains.governance.services.users.users_service_accounts import update_staff_account
# TODO: Module not yet created
# from domains.governance.services.users.users_service_accounts import list_pending_bank_accounts
# TODO: Module not yet created
# from domains.governance.services.users.users_service_accounts import delete_bank_account_record
from domains.governance.ports import verify_bank_account
# TODO: Module not yet created
# from domains.governance.services.settings.database_service import get_database_overview
from domains.governance.ports import get_authority_level
from domains.governance.ports import get_user_chain
from domains.governance.ports import get_all_subordinates
from domains.governance.ports import get_team_members
from domains.governance.ports import is_in_chain
from domains.governance.ports import can_manage
from domains.governance.ports import get_org_chart
from domains.governance.ports import get_home_org_unit
from domains.governance.ports import reassign_manager
from domains.governance.ports import backfill_authority_levels
from domains.governance.ports import APPROVAL_RULES, can_approve, get_approval_chain, require_approval, resolve_approvers
from domains.catalog.ports import get_banners
from domains.catalog.ports import get_banner_by_id
from domains.catalog.ports import create_banner
from domains.catalog.ports import update_banner
from domains.catalog.ports import delete_banner
from domains.catalog.ports import BannerCreate
from domains.catalog.ports import BannerUpdate
# TODO: Module not yet created
# from domains.governance.services.admin.export_service import export_users_csv, export_orders_csv, export_products_csv, export_coupons_csv, export_audit_logs_csv, export_transfer_csv, queue_export_job, download_export_job_result
from domains.orders.ports import get_promotion_config
from domains.orders.ports import update_promotion_config
from domains.orders.ports import list_promotion_tiers
from domains.orders.ports import create_promotion_tier
from domains.orders.ports import update_promotion_tier
from domains.orders.ports import delete_promotion_tier
from domains.orders.ports import preview_order_tier_discount
from domains.orders.ports import disputes_controller
from infrastructure.utils.backup import get_backup_manager
from infrastructure.database.schemas import FlashSaleCreate, FlashSaleOut
from orders.ports import get_all_flash_sales
from domains.orders.ports import create_flash_sale
from domains.orders.ports import update_flash_sale
from domains.orders.ports import delete_flash_sale

class BulkDeleteUsersBody(BaseModel):
    user_ids: List[int]

    @field_validator('user_ids')
    @classmethod
    def limit_bulk_size(cls, v: List[int]) -> List[int]:
        if len(v) > MAX_BULK_ITEMS:
            raise ValueError(f'Cannot process more than {MAX_BULK_ITEMS} items at once')
        return v

class BulkToggleActiveBody(BaseModel):
    user_ids: List[int]
    is_active: bool

    @field_validator('user_ids')
    @classmethod
    def limit_bulk_size(cls, v: List[int]) -> List[int]:
        if len(v) > MAX_BULK_ITEMS:
            raise ValueError(f'Cannot process more than {MAX_BULK_ITEMS} items at once')
        return v

class BulkUserRoleBody(BaseModel):
    user_ids: List[int]
    role: str

    @field_validator('user_ids')
    @classmethod
    def limit_bulk_size(cls, v: List[int]) -> List[int]:
        if len(v) > MAX_BULK_ITEMS:
            raise ValueError(f'Cannot process more than {MAX_BULK_ITEMS} items at once')
        return v

class ResetPasswordBody(BaseModel):
    new_password: str

class BulkOrderStatusBody(BaseModel):
    order_ids: List[int]
    status: str

    @field_validator('order_ids')
    @classmethod
    def limit_bulk_size(cls, v: List[int]) -> List[int]:
        if len(v) > MAX_BULK_ITEMS:
            raise ValueError(f'Cannot process more than {MAX_BULK_ITEMS} items at once')
        return v

class BulkOrderDeleteBody(BaseModel):
    order_ids: List[int]

    @field_validator('order_ids')
    @classmethod
    def limit_bulk_size(cls, v: List[int]) -> List[int]:
        if len(v) > MAX_BULK_ITEMS:
            raise ValueError(f'Cannot process more than {MAX_BULK_ITEMS} items at once')
        return v

class BulkProductDeleteBody(BaseModel):
    product_ids: List[int]

    @field_validator('product_ids')
    @classmethod
    def limit_bulk_size(cls, v: List[int]) -> List[int]:
        if len(v) > MAX_BULK_ITEMS:
            raise ValueError(f'Cannot process more than {MAX_BULK_ITEMS} items at once')
        return v

class BulkProductModerationBody(BaseModel):
    product_ids: List[int]
    action: str
    note: Optional[str] = None

    @field_validator('product_ids')
    @classmethod
    def limit_bulk_size(cls, v: List[int]) -> List[int]:
        if len(v) > MAX_BULK_ITEMS:
            raise ValueError(f'Cannot process more than {MAX_BULK_ITEMS} items at once')
        return v

class BulkSupplierVerifyBody(BaseModel):
    supplier_ids: List[int]
    action: str
    note: Optional[str] = None

    @field_validator('supplier_ids')
    @classmethod
    def limit_bulk_size(cls, v: List[int]) -> List[int]:
        if len(v) > MAX_BULK_ITEMS:
            raise ValueError(f'Cannot process more than {MAX_BULK_ITEMS} items at once')
        return v

class BulkSupplierLifecycleBody(BaseModel):
    supplier_ids: List[int]
    action: str
    note: Optional[str] = None
    badge_level: Optional[str] = None

    @field_validator('supplier_ids')
    @classmethod
    def limit_bulk_size(cls, v: List[int]) -> List[int]:
        if len(v) > MAX_BULK_ITEMS:
            raise ValueError(f'Cannot process more than {MAX_BULK_ITEMS} items at once')
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

    @field_validator('dispute_ids')
    @classmethod
    def limit_bulk_size(cls, v: List[int]) -> List[int]:
        if len(v) > MAX_BULK_ITEMS:
            raise ValueError(f'Cannot process more than {MAX_BULK_ITEMS} items at once')
        return v

class UpdateRolePermissionsIn(BaseModel):
    permissions: List[str]

class ReassignManagerBody(BaseModel):
    user_id: int
    new_manager_id: int | None = None

class ResourceApprovalCheckIn(BaseModel):
    resource_type: str
    amount: Optional[float] = None

def verify_payout_route(payout_id: int, data: dict, db: Session=Depends(get_db), current_admin: dict=Depends(require_admin_2fa_verified)):
    require_permission('payouts.verify', current_admin)
    from domains.finance.models.payments import Payout
    payout = db.query(Payout).filter(Payout.id == payout_id).first()
    amount = float(payout.amount) if payout and payout.amount is not None else None
    require_approval(db, current_admin['id'], 'payout', amount=amount)
    return verify_payout(payout_id, data, current_admin, db)

def admin_email_stats(db: Session=Depends(get_db), current_admin: dict=Depends(get_current_admin)):
    """Real email marketing statistics from the database."""
    require_permission('analytics.view', current_admin)
    from sqlalchemy import func as sqlfunc, case as sql_case
    from domains.comms.models.marketing import NewsletterSubscriber
    from domains.comms.models.marketing import EmailCampaign
    from domains.comms.models.marketing import CampaignRecipient
    total_subscribers = db.query(sqlfunc.count(NewsletterSubscriber.id)).filter(NewsletterSubscriber.is_active == True).scalar() or 0
    campaign_stats = db.query(sqlfunc.count(EmailCampaign.id).label('total'), sqlfunc.sum(sql_case((EmailCampaign.status == 'sending', 1), else_=0)).label('active')).first()
    total_sent = db.query(sqlfunc.count(CampaignRecipient.id)).filter(CampaignRecipient.sent_at.isnot(None)).scalar() or 0
    total_opened = db.query(sqlfunc.count(CampaignRecipient.id)).filter(CampaignRecipient.opened_at.isnot(None)).scalar() or 0
    total_clicked = db.query(sqlfunc.count(CampaignRecipient.id)).filter(CampaignRecipient.clicked_at.isnot(None)).scalar() or 0
    open_rate = round(total_opened / total_sent * 100, 1) if total_sent else 0
    click_rate = round(total_clicked / total_opened * 100, 1) if total_opened else 0
    recent_campaigns = db.query(EmailCampaign).order_by(EmailCampaign.created_at.desc()).limit(10).all()

    def _ser_campaign(c: EmailCampaign):
        recipient_count = db.query(sqlfunc.count(CampaignRecipient.id)).filter(CampaignRecipient.campaign_id == c.id).scalar() or 0
        return {'id': c.id, 'name': c.name, 'subject': c.subject, 'status': c.status, 'recipient_count': recipient_count, 'sent_count': recipient_count, 'opened_count': total_opened, 'clicked_count': total_clicked, 'send_at': c.send_at.isoformat() if c.send_at else None, 'sent_at': c.send_at.isoformat() if c.send_at else None, 'created_at': c.created_at.isoformat() if c.created_at else None}
    return {'total_subscribers': total_subscribers, 'active_campaigns': int(campaign_stats.active or 0), 'total_campaigns': int(campaign_stats.total or 0), 'total_sent': total_sent, 'open_rate': open_rate, 'click_rate': click_rate, 'recent_campaigns': [_ser_campaign(c) for c in recent_campaigns]}

def admin_logistics_overview(db: Session=Depends(get_db), current_admin: dict=Depends(get_current_admin)):
    """Admin overview of all shipments, carriers, and distribution channels."""
    require_permission('orders.manage', current_admin)
    from sqlalchemy import func as sqlfunc
    from domains.governance.models.admin import ShippingCarrier
    from domains.governance.models.admin import ShippingZone
    from domains.logistics.models.logistics import Shipment
    shipment_counts = db.query(Shipment.status, sqlfunc.count(Shipment.id).label('count')).group_by(Shipment.status).all()
    channel_counts = db.query(Shipment.distribution_channel, sqlfunc.count(Shipment.id).label('count')).filter(Shipment.distribution_channel.isnot(None)).group_by(Shipment.distribution_channel).all()
    carriers = db.query(ShippingCarrier).filter(ShippingCarrier.is_active == True).all()
    zones = db.query(ShippingZone).filter(ShippingZone.is_active == True).count()
    recent_shipments = db.query(Shipment).order_by(Shipment.updated_at.desc()).limit(20).all()

    def _ser_shipment(s: Shipment):
        return {'id': s.id, 'order_id': s.order_id, 'supplier_id': s.supplier_id, 'carrier_name': s.carrier_name, 'tracking_number': s.tracking_number, 'status': s.status, 'distribution_channel': s.distribution_channel, 'current_hub': s.current_hub, 'scan_code': s.scan_code, 'shipped_at': s.shipped_at.isoformat() if s.shipped_at else None, 'estimated_delivery': s.estimated_delivery.isoformat() if s.estimated_delivery else None, 'actual_delivery': s.actual_delivery.isoformat() if s.actual_delivery else None}
    return {'shipment_by_status': {s: c for (s, c) in shipment_counts}, 'shipment_by_channel': {ch: c for (ch, c) in channel_counts}, 'active_carriers': [{'id': c.id, 'name': c.name, 'code': c.code, 'is_global': c.supplier_id is None} for c in carriers], 'active_zones': zones, 'recent_shipments': [_ser_shipment(s) for s in recent_shipments]}

def admin_reset_demo_data(db: Session=Depends(get_db), current_admin: dict=Depends(get_current_admin)):
    """
    Clear all non-essential seed data  orders, products, reviews, communication
    data, coupons, and non-admin users  so the demo environment can be reset
    from the UI without SSH or terminal access.

    Admin user accounts (role=admin) are preserved.
    """
    require_admin(current_admin)
    app_env = getattr(settings, 'APP_ENV', None)
    if not app_env or app_env not in ('development', 'dev', 'test'):
        raise HTTPException(status_code=400, detail='Reset is only available in development/test environments')
    from datetime import datetime, timezone
    from sqlalchemy import text
    tables_to_clear = ['entity_chat_messages', 'entity_chat_threads', 'group_chat_messages', 'group_chat_members', 'group_chat_rooms', 'direct_chat_messages', 'direct_chat_rooms', 'internal_emails', 'email_folders', 'order_items', 'orders', 'reviews', 'order_logistics_allocations', 'shipments', 'wishlist_items', 'cart_items', 'coupon_usages', 'coupons', 'promotion_ledger_entries', 'promotion_order_tiers', 'product_variants', 'products', 'categories', 'audit_logs', 'notifications']
    deleted_counts: dict[str, int] = {}
    for table in tables_to_clear:
        try:
            if table not in Base.metadata.tables:
                deleted_counts[table] = -1
                continue
            result = db.execute(Base.metadata.tables[table].delete())
            deleted_counts[table] = result.rowcount or 0
        except Exception:
            deleted_counts[table] = -1
    non_admin_count = db.execute(text("DELETE FROM users WHERE role != 'admin'")).rowcount or 0
    deleted_counts['users_(non_admin)'] = non_admin_count
    try:
        db.execute(text('DELETE FROM sqlite_sequence'))
    except Exception:
        pass
    db.commit()
    total = sum((v for v in deleted_counts.values() if v >= 0))
    return {'detail': 'Demo data reset complete', 'tables_cleared': len(tables_to_clear) + 1, 'total_rows_deleted': total, 'counts': deleted_counts, 'note': 'Admin accounts preserved. Run seed_all.py to re-seed.'}

