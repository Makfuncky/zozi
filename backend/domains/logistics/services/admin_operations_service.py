"""Admin logistics / email-marketing aggregation service.

Holds the read-only DB aggregation that was previously inlined in
``routers/admin_logistics_operations.py`` for three admin endpoints:
``/email/stats``, ``/logistics/overview``, and the payout-verify amount lookup.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import func as sqlfunc, case as sql_case
from sqlalchemy.orm import Session

from models import (
    CampaignRecipient,
    EmailCampaign,
    NewsletterSubscriber,
    Payout,
    Shipment,
    ShippingCarrier,
    ShippingZone,
)


def get_payout_amount(db: Session, payout_id: int) -> Optional[float]:
    """Return the payout amount (or None) used for 2FA approval gating."""
    payout = db.query(Payout).filter(Payout.id == payout_id).first()
    if payout and payout.amount is not None:
        return float(payout.amount)
    return None


def get_email_stats(db: Session) -> dict:
    """Real email marketing statistics from the database."""
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

    def _ser_campaign(c: EmailCampaign) -> dict:
        recipient_count = db.query(sqlfunc.count(CampaignRecipient.id)).filter(
            CampaignRecipient.campaign_id == c.id
        ).scalar() or 0
        sent_count = db.query(sqlfunc.count(CampaignRecipient.id)).filter(
            CampaignRecipient.campaign_id == c.id,
            CampaignRecipient.sent_at.isnot(None),
        ).scalar() or 0
        opened_count = db.query(sqlfunc.count(CampaignRecipient.id)).filter(
            CampaignRecipient.campaign_id == c.id,
            CampaignRecipient.opened_at.isnot(None),
        ).scalar() or 0
        clicked_count = db.query(sqlfunc.count(CampaignRecipient.id)).filter(
            CampaignRecipient.campaign_id == c.id,
            CampaignRecipient.clicked_at.isnot(None),
        ).scalar() or 0
        return {
            "id": c.id,
            "name": c.name,
            "subject": c.subject,
            "status": c.status,
            "recipient_count": recipient_count,
            "sent_count": sent_count,
            "opened_count": opened_count,
            "clicked_count": clicked_count,
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


def get_logistics_overview(db: Session) -> dict:
    """Admin overview of all shipments, carriers, and distribution channels."""
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

    def _ser_shipment(s: Shipment) -> dict:
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
