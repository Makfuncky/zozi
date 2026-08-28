from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session

from domains.governance.services.settings.misc_service import (
    get_audit_log_page,
    get_available_audit_actions,
)
from infrastructure.security.dependencies import (
    require_admin,
)
# from domains.orders.ports import get_promotion_config, list_promotion_tiers, preview_order_tier_discount  # unused
# from domains.orders.ports import create_promotion_tier, delete_promotion_tier, update_promotion_config, update_promotion_tier  # unused
# from domains.orders.ports import get_all_flash_sales  # unused
# from domains.orders.ports import create_flash_sale, delete_flash_sale, update_flash_sale  # unused
from infrastructure.database.database import get_db
from infrastructure.database.schemas import AuditLogPage, BulkUpdateStaffBody, CouponSchema, CreateStaffAccount, ListPage, UpdateStaffAccount
from infrastructure.database.schemas import Order as OrderSchema
from infrastructure.database.schemas import Product as ProductSchema
from infrastructure.utils.constants import MAX_BULK_ITEMS
from infrastructure.database.schemas import FlashSaleCreate, FlashSaleOut
# from infrastructure.security.auth import require_permission  # module not available
from domains.governance.exceptions import ValidationError


def admin_email_stats(db: Session, current_admin: dict):
    """Real email marketing statistics from the database."""
    require_permission('analytics.view', current_admin)
    from sqlalchemy import case as sql_case
    from sqlalchemy import func as sqlfunc
    from domains.comms.models.marketing import CampaignRecipient
    from domains.comms.models.marketing import EmailCampaign
    from domains.comms.models.marketing import NewsletterSubscriber
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


def admin_supplier_documents(supplier_id: Optional[int], status: Optional[str], doc_type: Optional[str], page: int, page_size: int, db: Session, current_admin: dict):
    """Admin: view all supplier KYC documents."""
    require_permission('moderation.suppliers', current_admin)
    import domains.suppliers.services as _sdc
    return _sdc.admin_list_documents(current_admin, db, supplier_id=supplier_id, status=status, doc_type=doc_type, limit=page_size, offset=(page - 1) * page_size)


def admin_review_document(doc_id: int, data: dict, db: Session, current_admin: dict):
    """Admin: approve or reject a supplier document."""
    require_permission('moderation.suppliers', current_admin)
    import domains.suppliers.services as _sdc
    return _sdc.admin_review_document(doc_id, data, current_admin, db)


def admin_reset_demo_data(db: Session, current_admin: dict):
    """
    Clear all non-essential seed data  orders, products, reviews, communication
    data, coupons, and non-admin users  so the demo environment can be reset
    from the UI without SSH or terminal access.

    Admin user accounts (role=admin) are preserved.
    """
    require_admin(current_admin)
    from infrastructure.utils.config import settings
    app_env = getattr(settings, 'APP_ENV', None)
    if not app_env or app_env not in ('development', 'dev', 'test'):
        raise ValidationError('app_env', 'Reset is only available in development/test environments')
    from domains.governance.services.settings.misc_write_service import reset_demo_data
    return reset_demo_data(db)


def __getattr__(name):
    _LAZY = {'APPROVAL_RULES': 'services.security.approval_matrix_service', 'can_approve': 'services.security.approval_matrix_service', 'get_approval_chain': 'services.security.approval_matrix_service', 'require_approval': 'services.security.approval_matrix_service', 'resolve_approvers': 'services.security.approval_matrix_service'}
    if name in _LAZY:
        import importlib
        return getattr(importlib.import_module(_LAZY[name]), name)
    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')

