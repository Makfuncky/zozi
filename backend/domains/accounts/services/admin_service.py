"""Auto-migrated service logic from routers/admin.py."""
from __future__ import annotations
from services.admin.admin_logistics_operations_service import (
    BulkUserRoleBody,
    BulkOrderStatusBody,
    PromotionTierBody,
    BulkToggleActiveBody,
    BulkProductDeleteBody,
    BulkSupplierVerifyBody,
    ResetPasswordBody,
    UpdateRolePermissionsIn,
    PromotionTierUpdateBody,
    BulkSupplierLifecycleBody,
    PromotionConfigBody,
    AdminDisputeBulkActionBody,
    BulkOrderDeleteBody,
    BulkProductModerationBody,
    ResourceApprovalCheckIn,
    ReassignManagerBody,
    PromotionPreviewBody,
    BulkDeleteUsersBody,
)
from datetime import datetime
from typing import List, Optional
from fastapi import Body, Depends, HTTPException, Path, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session
from modules.orders.routers import disputes_controller
from modules.admin.routers.auth import bulk_delete_users_admin, bulk_manage_suppliers, bulk_product_moderation, bulk_supplier_verification, bulk_toggle_users_active, bulk_update_order_status_admin, bulk_update_staff_accounts, bulk_update_users_role, create_coupon, create_staff_account, delete_bank_account_record, delete_coupon, delete_order_admin, delete_product_admin, delete_staff_account, delete_user_admin, force_reset_password_admin, get_all_orders, get_all_products, get_all_suppliers, get_all_users, get_analytics, get_analytics_timeseries, get_audit_log_page, get_available_audit_actions, get_chatbot_analytics, get_current_admin, get_current_user, get_customer_insights, get_database_overview, get_hierarchy_permissions, get_pending_products, get_pending_suppliers, get_staff_permission_catalog, get_supplier_comparison, get_ticket_detail, get_top_products_analytics, get_user_growth_analytics, list_coupons, list_pending_bank_accounts, list_pending_payouts, list_staff_accounts, list_tickets, refund_order, reject_product, reject_supplier, reply_to_ticket, require_admin, require_admin_2fa_verified, require_permission, restore_product_admin, toggle_product_badge, toggle_user_active, update_coupon, update_order_status, update_order_tracking, update_role_permissions, update_staff_account, update_ticket_status, update_user_role, verify_bank_account, verify_payout, verify_supplier
from controllers.catalog.banner_controller import BannerCreate, BannerUpdate, create_banner, delete_banner, get_banner_by_id, update_banner
from services.core.export_service import download_export_job_result, export_audit_logs_csv, export_coupons_csv, export_orders_csv, export_products_csv, export_transfer_csv, export_users_csv, queue_export_job
from modules.commerce.routers.promotion_controller import create_promotion_tier, delete_promotion_tier, get_promotion_config, list_promotion_tiers, preview_order_tier_discount, update_promotion_config, update_promotion_tier
from infrastructure.database.database import get_db
from infrastructure.database.schemas import AuditLogPage, BulkUpdateStaffBody, CouponSchema, CreateStaffAccount, ListPage, UpdateStaffAccount
from infrastructure.database.schemas import Order as OrderSchema
from infrastructure.database.schemas import Product as ProductSchema
from services.hierarchy.hierarchy_service import backfill_authority_levels, get_all_subordinates, get_authority_level, get_org_chart, get_team_members, get_user_chain, is_in_chain, reassign_manager
from services.hierarchy.hierarchy_service import can_manage as hierarchy_can_manage_service
from services.common.misc_write_service import reset_demo_data
from infrastructure.utils.backup import get_backup_manager
from infrastructure.utils.constants import MAX_BULK_ITEMS















from modules.commerce.routers.flash_sale_controller import create_flash_sale, delete_flash_sale, get_all_flash_sales, update_flash_sale
from infrastructure.database.schemas import FlashSaleCreate, FlashSaleOut




def admin_email_stats(db: Session, current_admin: dict):
    """Real email marketing statistics from the database."""
    require_permission('analytics.view', current_admin)
    from sqlalchemy import case as sql_case
    from sqlalchemy import func as sqlfunc
    from _legacy.models import CampaignRecipient, EmailCampaign, NewsletterSubscriber
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

def admin_logistics_overview(db: Session, current_admin: dict):
    """Admin overview of all shipments, carriers, and distribution channels."""
    require_permission('orders.manage', current_admin)
    from sqlalchemy import func as sqlfunc
    from _legacy.models import Shipment, ShippingCarrier, ShippingZone
    shipment_counts = db.query(Shipment.status, sqlfunc.count(Shipment.id).label('count')).group_by(Shipment.status).all()
    channel_counts = db.query(Shipment.distribution_channel, sqlfunc.count(Shipment.id).label('count')).filter(Shipment.distribution_channel.isnot(None)).group_by(Shipment.distribution_channel).all()
    carriers = db.query(ShippingCarrier).filter(ShippingCarrier.is_active == True).all()
    zones = db.query(ShippingZone).filter(ShippingZone.is_active == True).count()
    recent_shipments = db.query(Shipment).order_by(Shipment.updated_at.desc()).limit(20).all()

    def _ser_shipment(s: Shipment):
        return {'id': s.id, 'order_id': s.order_id, 'supplier_id': s.supplier_id, 'carrier_name': s.carrier_name, 'tracking_number': s.tracking_number, 'status': s.status, 'distribution_channel': s.distribution_channel, 'current_hub': s.current_hub, 'scan_code': s.scan_code, 'shipped_at': s.shipped_at.isoformat() if s.shipped_at else None, 'estimated_delivery': s.estimated_delivery.isoformat() if s.estimated_delivery else None, 'actual_delivery': s.actual_delivery.isoformat() if s.actual_delivery else None}
    return {'shipment_by_status': {s: c for (s, c) in shipment_counts}, 'shipment_by_channel': {ch: c for (ch, c) in channel_counts}, 'active_carriers': [{'id': c.id, 'name': c.name, 'code': c.code, 'is_global': c.supplier_id is None} for c in carriers], 'active_zones': zones, 'recent_shipments': [_ser_shipment(s) for s in recent_shipments]}

def admin_supplier_documents(supplier_id: Optional[int], status: Optional[str], doc_type: Optional[str], page: int, page_size: int, db: Session, current_admin: dict):
    """Admin: view all supplier KYC documents."""
    require_permission('moderation.suppliers', current_admin)
    import controllers.supplier_document_controller as _sdc
    return _sdc.admin_list_documents(current_admin, db, supplier_id=supplier_id, status=status, doc_type=doc_type, limit=page_size, offset=(page - 1) * page_size)

def admin_review_document(doc_id: int, data: dict, db: Session, current_admin: dict):
    """Admin: approve or reject a supplier document."""
    require_permission('moderation.suppliers', current_admin)
    import controllers.supplier_document_controller as _sdc
    return _sdc.admin_review_document(doc_id, data, current_admin, db)

def admin_reset_demo_data(db: Session, current_admin: dict):
    """
    Clear all non-essential seed data — orders, products, reviews, communication
    data, coupons, and non-admin users — so the demo environment can be reset
    from the UI without SSH or terminal access.

    Admin user accounts (role=admin) are preserved.
    """
    require_admin(current_admin)
    app_env = getattr(settings, 'APP_ENV', None)
    if not app_env or app_env not in ('development', 'dev', 'test'):
        raise HTTPException(status_code=400, detail='Reset is only available in development/test environments')
    return reset_demo_data(db)

def __getattr__(name):
    _LAZY = {'APPROVAL_RULES': 'services.security.approval_matrix_service', 'can_approve': 'services.security.approval_matrix_service', 'get_approval_chain': 'services.security.approval_matrix_service', 'require_approval': 'services.security.approval_matrix_service', 'resolve_approvers': 'services.security.approval_matrix_service'}
    if name in _LAZY:
        import importlib
        return getattr(importlib.import_module(_LAZY[name]), name)
    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
from services.admin.admin_identity_operations_api_service import list_users  # [MIGRATION COMPAT] re-export relocated symbol













from services.admin.admin_logistics_operations_service import set_user_role  # [MIGRATION COMPAT] re-export relocated symbol










from services.admin.admin_logistics_operations_service import toggle_user_status  # [MIGRATION COMPAT] re-export relocated symbol












from services.admin.admin_logistics_operations_service import bulk_delete_users  # [MIGRATION COMPAT] re-export relocated symbol














from services.admin.admin_logistics_operations_service import bulk_toggle_users_active_route  # [MIGRATION COMPAT] re-export relocated symbol


# === auto-wiring re-exports (migration repair) ===
from services.admin.admin_logistics_operations_service import (
    admin_approve_bank_account,
    admin_country_dashboard,
    admin_create_banner,
    admin_create_logistics_partner,
    admin_database_overview,
    admin_delete_bank_account,
    admin_delete_banner,
    admin_download_backup,
    admin_download_export_job,
    admin_export_audit_logs,
    admin_export_cod_remittance_transfers,
    admin_export_coupons,
    admin_export_logistics_payout_transfers,
    admin_export_orders,
    admin_export_products,
    admin_export_supplier_payout_transfers,
    admin_export_users,
    admin_get_banner,
    admin_invoices_overview,
    admin_list_backups,
    admin_list_banners,
    admin_list_pending_bank_accounts,
    admin_logistics_partners,
    admin_reject_bank_account,
    admin_reset_password,
    admin_rotate_encryption_key,
    admin_run_backup_restore_drill,
    admin_trigger_backup,
    admin_update_banner,
    admin_update_logistics_partner,
    analytics,
    analytics_chatbot,
    analytics_timeseries,
    analytics_top_products,
    analytics_user_growth,
    approve_product_route,
    approve_supplier,
    audit_log_actions,
    bulk_admin_dispute_action,
    bulk_delete_orders,
    bulk_delete_products,
    bulk_manage_supplier_lifecycle,
    bulk_update_orders_status,
    bulk_update_staff,
    bulk_update_users_role_route,
    bulk_verify_suppliers,
    check_approval_eligibility,
    create_coupon_route,
    create_flash_sale_route,
    create_promotion_tier_route,
    create_staff,
    customer_insights,
    decline_supplier,
    delete_coupon_route,
    delete_flash_sale_route,
    delete_order_route,
    delete_product,
    delete_promotion_tier_route,
    delete_staff,
    delete_user,
    get_admin_dispute,
    get_approval_matrix_rules,
    get_checkout_config,
    get_country_audit_trail,
    get_hierarchy_permissions_route,
    get_pending_payouts_route,
    get_promotion_config_route,
    get_resource_approvers,
    get_ticket,
    get_user_approval_chain,
    hierarchy_authority_level,
    hierarchy_backfill_authority_levels,
    hierarchy_can_manage,
    hierarchy_chain,
    hierarchy_in_chain,
    hierarchy_org_chart,
    hierarchy_reassign_manager,
    hierarchy_subordinates,
    hierarchy_team_members,
    list_admin_disputes,
    list_all_coupons,
    list_all_suppliers,
    list_all_tickets,
    list_audit_logs,
    list_orders,
    list_pending_products,
    list_pending_suppliers,
    list_products,
    list_promotion_tiers_route,
    patch_admin_dispute,
    preview_promotion_route,
    refresh_supplier_badge,
    refund_order_route,
    reject_product_route,
    reply_ticket,
    restore_product,
    set_order_status,
    set_order_tracking,
    set_product_badge,
    set_supplier_badge,
    set_ticket_status,
    staff_permission_catalog,
    supplier_comparison,
    update_coupon_route,
    update_flash_sale_route,
    update_promotion_config_route,
    update_promotion_tier_route,
    update_role_permissions_route,
    update_staff,
    verify_payout_route
)
from services.admin.admin_geography_audit_service import (
    generate_legal_contract,
    list_staff
)
from services.admin.admin_catalog_operations_service import (
    bulk_moderate_products
)
from services.admin.admin_commerce_configuration_service import (
    list_flash_sales
)


