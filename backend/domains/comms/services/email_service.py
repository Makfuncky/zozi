"""Auto-migrated service logic from routers/email.py."""
from __future__ import annotations

from __future__ import annotations
from domains.comms.services.email_management_service import _serialize_template

import logging

from typing import Annotated, Any, Dict, List, Optional

from fastapi import Body, Depends, HTTPException, Query, Request

from fastapi.responses import Response

from pydantic import BaseModel

from sqlalchemy import desc

from sqlalchemy.orm import Session

from modules.admin.routers.auth import require_roles
from infrastructure.database.database import get_db

from domains.comms.models.marketing import (
    EmailCampaign,
    EmailRuntimeConfig,
    EmailSuppression,
    EmailTemplate,
)

from domains.comms.services.email_gateway import EmailGateway

from domains.comms.services.transactional_email_service import enqueue_invoice_email
from domains.comms.services.transactional_email_service import enqueue_low_stock_alert_email
from domains.comms.services.transactional_email_service import enqueue_order_created_email

from infrastructure.utils.datetime_utils import utcnow as _utcnow

logger = logging.getLogger(__name__)


AdminUser = Annotated[dict, Depends(require_roles("admin"))]

AdminOrSuperAdminUser = Annotated[dict, Depends(require_roles("admin", "superadmin"))]

_TRANSPARENT_GIF = (
    b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01"
    b"\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
)

class SendEmailPayload(BaseModel):
    to: str
    subject: str
    body: str
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None
    is_html: bool = True

class SendTransactionalPayload(BaseModel):
    to: str
    template: str
    variables: Dict[str, Any] = {}


def _email_runtime_to_dict(cfg: EmailRuntimeConfig) -> dict:
    resend_key = bool(cfg.resend_api_key)
    resend_secret = bool(cfg.resend_webhook_secret)
    return {
        "id": cfg.id,
        "provider": cfg.provider,
        "active_provider": cfg.provider,
        "source": "db",
        "available": True,
        "live": cfg.provider not in ("disabled", None),
        "preview_only": cfg.provider == "environment",
        "supports_webhooks": True,
        "smtp_host": cfg.smtp_host,
        "smtp_port": cfg.smtp_port or 587,
        "smtp_username": cfg.smtp_username,
        "smtp_use_tls": cfg.smtp_use_tls,
        "smtp_use_ssl": cfg.smtp_use_ssl,
        "smtp_timeout_seconds": cfg.smtp_timeout_seconds or 15,
        "email_from_default": cfg.email_from_default,
        "email_from_promotional": cfg.email_from_promotional,
        "email_from_transactional": cfg.email_from_transactional,
        "email_from_notification": cfg.email_from_notification,
        "email_from_alert": cfg.email_from_alert,
        "email_from_verification": cfg.email_from_verification,
        "email_from_login_verification": cfg.email_from_login_verification,
        "email_from_password_reset": cfg.email_from_password_reset,
        "resend_api_key_configured": resend_key,
        "resend_webhook_secret_configured": resend_secret,
        "smtp_password_configured": bool(cfg.smtp_password),
    }

class InternalEmailPayload(BaseModel):
    to: List[int]
    subject: str
    body: str
    cc: Optional[List[int]] = None
    attachment_ids: Optional[List[int]] = None

class ExternalEmailPayload(BaseModel):
    to: str
    subject: str
    body: str
    template_id: Optional[str] = None

async def resend_webhook(request: Request, db: Session):
    """Receive delivery event webhooks from Resend."""
    try:
        payload = await request.json()
        event_type = payload.get("type", "")
        email_id = payload.get("data", {}).get("email_id", "")
        logger.info("Email webhook: type=%s email_id=%s", event_type, email_id)
    except Exception as exc:
        logger.debug("Webhook parse error: %s", exc)
    return {"status": "received"}

def send_email(current_user: AdminUser, payload: SendEmailPayload, db: Session):
    """Send an email via the configured email provider."""
    gateway = EmailGateway()
    result = gateway.send_external_email(
        to_email=payload.to,
        subject=payload.subject,
        body=payload.body,
        cc=payload.cc or [],
        bcc=payload.bcc or [],
        is_html=payload.is_html,
    )
    return {"status": result.get("status", "sent"), "email_id": result.get("email_id")}

def send_transactional(current_user: AdminUser, payload: SendTransactionalPayload):
    """Send a transactional email using a predefined template."""
    templates = {
        "order_created": lambda: enqueue_order_created_email(payload.to, payload.variables),
        "invoice": lambda: enqueue_invoice_email(payload.to, payload.variables),
        "low_stock": lambda: enqueue_low_stock_alert_email(payload.to, payload.variables),
    }
    handler = templates.get(payload.template)
    if not handler:
        raise HTTPException(status_code=400, detail=f"Unknown template: {payload.template}")
    handler()
    return {"status": "queued", "template": payload.template}

def send_from_alias(current_user: AdminUser, alias_key: str, to: str, subject: str, body: str):
    """Send email from a role-based alias (e.g., kyc.ksa@zozi.com)."""
    gateway = EmailGateway()
    result = gateway.send_from_alias(alias_key, to, subject, body)
    return {"status": result.get("status", "sent")}

def send_bulk(to_emails: List[str], subject: str, body: str, current_user: AdminOrSuperAdminUser):
    """Send bulk email with DLP protection."""
    gateway = EmailGateway()
    results = gateway.send_bulk_email(to_emails, subject, body)
    return {
        "total": len(to_emails),
        "sent": sum(1 for r in results if r.get("status") == "sent"),
        "failed": sum(1 for r in results if r.get("status") != "sent"),
        "results": results,
    }

def list_templates(current_user: AdminUser, db: Session):
    templates = db.query(EmailTemplate).order_by(desc(EmailTemplate.created_at)).all()
    return [_serialize_template(t) for t in templates]

def list_campaigns(current_user: AdminUser, db: Session):
    from domains.comms.models.marketing import EmailCampaign
    campaigns = db.query(EmailCampaign).order_by(desc(EmailCampaign.created_at)).all()
    return [
        {
            "id": c.id,
            "name": c.name,
            "subject": c.subject,
            "status": c.status,
            "sent_count": c.sent_count,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in campaigns
    ]

def list_suppressions(status: Optional[str], current_user: AdminOrSuperAdminUser, db: Session):
    q = db.query(EmailSuppression)
    if status:
        q = q.filter(EmailSuppression.status == status)
    suppressions = q.all()
    return [
        {
            "id": s.id,
            "email": s.email,
            "reason": s.reason,
            "source": s.source,
            "provider": s.provider,
            "status": s.status,
            "notes": s.notes,
            "suppressed_at": s.suppressed_at.isoformat() if s.suppressed_at else None,
            "last_event_at": s.last_event_at.isoformat() if s.last_event_at else None,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in suppressions
    ]

def update_suppression(suppression_id: int, body: Dict[str, Any], current_user: AdminOrSuperAdminUser, db: Session):
    s = db.query(EmailSuppression).filter(EmailSuppression.id == suppression_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Suppression not found")
    if "status" in body:
        s.status = body["status"]
        if body["status"] == "active" and not s.suppressed_at:
            s.suppressed_at = _utcnow()
        s.last_event_at = _utcnow()
    if "reason" in body:
        s.reason = body["reason"]
    if "notes" in body:
        s.notes = body["notes"]
    db.commit()
    db.refresh(s)
    return {
        "id": s.id,
        "email": s.email,
        "reason": s.reason,
        "source": s.source,
        "provider": s.provider,
        "status": s.status,
        "notes": s.notes,
        "suppressed_at": s.suppressed_at.isoformat() if s.suppressed_at else None,
        "last_event_at": s.last_event_at.isoformat() if s.last_event_at else None,
    }

def create_campaign(payload: Dict[str, Any], current_user: AdminUser, db: Session):
    campaign = EmailCampaign(
        name=payload.get("name", "Untitled Campaign"),
        subject=payload.get("subject", ""),
        status=payload.get("status", "draft"),
        target_audience=payload.get("target_audience"),
        country_code=payload.get("country_code"),
        created_by=current_user.get("id") if isinstance(current_user, dict) else None,
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return {
        "id": campaign.id,
        "name": campaign.name,
        "subject": campaign.subject,
        "status": campaign.status,
        "created_at": campaign.created_at.isoformat() if campaign.created_at else None,
    }

def create_template(payload: Dict[str, Any], current_user: AdminUser, db: Session):
    template = EmailTemplate(
        name=payload.get("name", ""),
        subject=payload.get("subject", ""),
        content=payload.get("content"),
        template_type=payload.get("template_type", "marketing"),
        created_by=current_user.get("id") if isinstance(current_user, dict) else None,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return _serialize_template(template)

def update_template(template_id: int, payload: Dict[str, Any], current_user: AdminUser, db: Session):
    template = db.query(EmailTemplate).filter(EmailTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    if "name" in payload:
        template.name = payload["name"]
    if "subject" in payload:
        template.subject = payload["subject"]
    if "content" in payload:
        template.content = payload["content"]
    if "template_type" in payload:
        template.template_type = payload["template_type"]
    db.commit()
    db.refresh(template)
    return _serialize_template(template)

def delete_template(template_id: int, current_user: AdminUser, db: Session):
    template = db.query(EmailTemplate).filter(EmailTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    db.delete(template)
    db.commit()
    return {"message": "Template deleted", "id": template_id}

def get_email_runtime_config(current_user: AdminUser, db: Session):
    cfg = db.query(EmailRuntimeConfig).order_by(EmailRuntimeConfig.id.asc()).first()
    if not cfg:
        cfg = EmailRuntimeConfig(provider="environment", smtp_port=587)
        db.add(cfg)
        db.commit()
        db.refresh(cfg)
    return _email_runtime_to_dict(cfg)

def update_email_runtime_config(payload: Dict[str, Any], current_user: AdminUser, db: Session):
    cfg = db.query(EmailRuntimeConfig).order_by(EmailRuntimeConfig.id.asc()).first()
    if not cfg:
        cfg = EmailRuntimeConfig()
        db.add(cfg)
    simple_fields = [
        "provider", "smtp_host", "smtp_port", "smtp_username",
        "smtp_use_tls", "smtp_use_ssl", "smtp_timeout_seconds",
        "email_from_default", "email_from_promotional", "email_from_transactional",
        "email_from_notification", "email_from_alert", "email_from_verification",
        "email_from_login_verification", "email_from_password_reset",
    ]
    for field in simple_fields:
        if field in payload:
            setattr(cfg, field, payload[field])
    # Only overwrite secrets when a non-empty value is supplied.
    if payload.get("resend_api_key"):
        cfg.resend_api_key = payload["resend_api_key"]
    if payload.get("resend_webhook_secret"):
        cfg.resend_webhook_secret = payload["resend_webhook_secret"]
    if payload.get("smtp_password"):
        cfg.smtp_password = payload["smtp_password"]
    db.commit()
    db.refresh(cfg)
    return _email_runtime_to_dict(cfg)

def test_send_email(payload: Dict[str, Any], current_user: AdminUser, db: Session):
    to_email = payload.get("to_email") or (payload.get("to") if isinstance(payload.get("to"), str) else None)
    if not to_email:
        raise HTTPException(status_code=422, detail="to_email is required")
    purpose = payload.get("purpose", "transactional")
    subject = payload.get("subject") or f"ZOZI test email ({purpose})"
    gateway = EmailGateway(db)
    sender_id = current_user.get("id") if isinstance(current_user, dict) else None
    result = gateway.send_external_email(
        to_email=to_email,
        subject=subject,
        body=f"<p>This is a test email from ZOZI (purpose: {purpose}).</p>",
        sender_id=sender_id,
    )
    return {
        "provider": result.get("provider", "unknown"),
        "from_address": result.get("from_address"),
        "preview_only": result.get("preview_only", False),
        "status": result.get("status", "sent"),
    }

async def track_open(email_id: str, user_id: int):
    """Tracking pixel for email open detection."""
    try:
        from infrastructure.utils.email_service import record_email_delivery_event
        record_email_delivery_event(email_id=email_id, user_id=user_id, event_type="open")
    except Exception:
        pass
    return Response(content=_TRANSPARENT_GIF, media_type="image/gif")

def send_internal_email(payload: InternalEmailPayload, current_user: AdminUser, db: Session):
    """Send an internal email and store it in the employee inbox."""
    gateway = EmailGateway(db)
    sender_id = current_user.get("id") if isinstance(current_user, dict) else None
    return gateway.send_internal_email(
        to_user_ids=payload.to,
        subject=payload.subject,
        body=payload.body,
        sender_id=sender_id or 0,
    )

def get_my_inbox(folder: str, limit: int, offset: int, current_user: AdminUser, db: Session):
    """Get internal emails for the current admin/staff user."""
    from domains.hr.services.employee_communication_service import get_inbox
    employee_id = current_user.get("id") if isinstance(current_user, dict) else 0
    return get_inbox(db, employee_id=employee_id, folder=folder, limit=limit, offset=offset)


