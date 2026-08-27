"""Comms marketing campaign service — admin operations."""
from __future__ import annotations

from sqlalchemy import func, case as sql_case
from sqlalchemy.orm import Session

from domains.comms.models.marketing import EmailCampaign, CampaignRecipient, NewsletterSubscriber
from infrastructure.utils.pagination import keyset_paginate


def list_all_campaigns(db: Session, limit: int, cursor: str | None) -> dict:
    query = db.query(EmailCampaign)
    return keyset_paginate(query, sort_keys=[(EmailCampaign.id, "asc")], cursor=cursor, page_size=limit)


def admin_email_metrics(db: Session) -> dict:
    total_subscribers = db.query(func.count(NewsletterSubscriber.id)).filter(NewsletterSubscriber.is_active == True).scalar() or 0
    campaign_stats = db.query(
        func.count(EmailCampaign.id).label("total"),
        func.sum(sql_case((EmailCampaign.status == "sending", 1), else_=0)).label("active"),
        func.count(CampaignRecipient.id).label("total_sent"),
    ).first()
    return {
        "total_subscribers": total_subscribers,
        "active_campaigns": int(campaign_stats.active or 0),
        "total_campaigns": int(campaign_stats.total or 0),
        "total_sent": int(campaign_stats.total_sent or 0),
    }


def list_campaigns(db: Session, country_code: str, limit: int, cursor: str | None) -> dict:
    q = db.query(EmailCampaign).filter(EmailCampaign.country_code == country_code.upper())
    return keyset_paginate(q, sort_keys=[(EmailCampaign.id, "asc")], cursor=cursor, page_size=limit)


def create_campaign(db: Session, country_code: str, payload: dict) -> EmailCampaign:
    allowed = {"name", "subject", "status", "send_at", "created_by", "country_code"}
    data = {k: v for k, v in payload.items() if k in allowed and v is not None}
    data["country_code"] = country_code.upper()
    c = EmailCampaign(**data)
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


def delete_campaign(db: Session, country_code: str, campaign_id: int) -> dict:
    c = db.query(EmailCampaign).filter(
        EmailCampaign.id == campaign_id,
        EmailCampaign.country_code == country_code.upper(),
    ).first()
    if not c:
        from fastapi import HTTPException
        raise HTTPException(404)
    db.delete(c)
    db.commit()
    return {"message": "Deleted"}
