"""
Email Router — send, manage templates, and handle delivery webhooks.
"""

from __future__ import annotations

import logging
from typing import Annotated, Any, List, Optional, Dict

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import desc

from data.controllers_admin_controller import require_roles
from data.db import get_db
from routers.auth import get_current_user
from services.email_gateway import EmailGateway
from services.transactional_email_service import (
    enqueue_order_created_email,
    enqueue_invoice_email,
    enqueue_low_stock_alert_email,
    enqueue_order_confirmation_email,
)
from models.marketing import (
    EmailCampaign,
    EmailTemplate,
    EmailSuppression,
    EmailRuntimeConfig,
)
from utils.config import settings
from utils.datetime_utils import utcnow as _utcnow

from services.write_helpers import add_and_flush, commit_and_refresh, commit_only, delete_only
logger = logging.getLogger(__name__)

router = APIRouter()
public_router = APIRouter()

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


@public_router.post("/webhooks/resend")
async def resend_webhook(request: Request, db: Session = Depends(get_db)):
    """Receive delivery event webhooks from Resend."""
    try:
        payload = await request.json()
        event_type = payload.get("type", "")
        email_id = payload.get("data", {}).get("email_id", "")
        logger.info("Email webhook: type=%s email_id=%s", event_type, email_id)
    except Exception as exc:
        logger.debug("Webhook parse error: %s", exc)
    return {"status": "received"}


@router.post("/send")
def send_email(
    current_user: AdminUser,
    payload: SendEmailPayload,
    db: Session = Depends(get_db),
):
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


@router.post("/send/transactional")
def send_transactional(
    current_user: AdminUser,
    payload: SendTransactionalPayload,
):
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


@router.post("/send/alias")
def send_from_alias(
    current_user: AdminUser,
    alias_key: str = Body(...),
    to: str = Body(...),
    subject: str = Body(...),
    body: str = Body(...),
):
    """Send email from a role-based alias (e.g., kyc.ksa@zozi.com)."""
    gateway = EmailGateway()
    result = gateway.send_from_alias(alias_key, to, subject, body)
    return {"status": result.get("status", "sent")}


@router.post("/send/bulk")
def send_bulk(
    to_emails: List[str] = Body(...),
    subject: str = Body(...),
    body: str = Body(...),
    current_user: AdminOrSuperAdminUser = None,
):
    """Send bulk email with DLP protection."""
    gateway = EmailGateway()
    results = gateway.send_bulk_email(to_emails, subject, body)
    return {
        "total": len(to_emails),
        "sent": sum(1 for r in results if r.get("status") == "sent"),
        "failed": sum(1 for r in results if r.get("status") != "sent"),
        "results": results,
    }


@router.get("/templates")
def list_templates(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: AdminUser = None,
    db: Session = Depends(get_db),
):
    templates = db.query(EmailTemplate).order_by(desc(EmailTemplate.created_at)).offset(skip).limit(limit).all()
    return [_serialize_template(t) for t in templates]


@router.get("/campaigns")
def list_campaigns(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: AdminUser = None,
    db: Session = Depends(get_db),
):
    from models.marketing import EmailCampaign
    campaigns = db.query(EmailCampaign).order_by(desc(EmailCampaign.created_at)).offset(skip).limit(limit).all()
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


@router.get("/suppressions")
def list_suppressions(
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: AdminOrSuperAdminUser = None,
    db: Session = Depends(get_db),
):
    q = db.query(EmailSuppression)
    if status:
        q = q.filter(EmailSuppression.status == status)
    suppressions = q.offset(skip).limit(limit).all()
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


@router.patch("/suppressions/{suppression_id}")
def update_suppression(
    suppression_id: int,
    body: Dict[str, Any] = Body(default={}),
    current_user: AdminOrSuperAdminUser = None,
    db: Session = Depends(get_db),
):
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
    commit_and_refresh(db, s)
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


@router.post("/campaigns")
def create_campaign(
    payload: Dict[str, Any] = Body(default={}),
    current_user: AdminUser = None,
    db: Session = Depends(get_db),
):
    campaign = EmailCampaign(
        name=payload.get("name", "Untitled Campaign"),
        subject=payload.get("subject", ""),
        status=payload.get("status", "draft"),
        target_audience=payload.get("target_audience"),
        country_code=payload.get("country_code"),
        created_by=current_user.get("id") if isinstance(current_user, dict) else None,
    )
    add_and_flush(db, campaign)
    commit_and_refresh(db, campaign)
    return {
        "id": campaign.id,
        "name": campaign.name,
        "subject": campaign.subject,
        "status": campaign.status,
        "created_at": campaign.created_at.isoformat() if campaign.created_at else None,
    }


@router.post("/templates")
def create_template(
    payload: Dict[str, Any] = Body(default={}),
    current_user: AdminUser = None,
    db: Session = Depends(get_db),
):
    template = EmailTemplate(
        name=payload.get("name", ""),
        subject=payload.get("subject", ""),
        content=payload.get("content"),
        template_type=payload.get("template_type", "marketing"),
        created_by=current_user.get("id") if isinstance(current_user, dict) else None,
    )
    add_and_flush(db, template)
    commit_and_refresh(db, template)
    return _serialize_template(template)


@router.put("/templates/{template_id}")
def update_template(
    template_id: int,
    payload: Dict[str, Any] = Body(default={}),
    current_user: AdminUser = None,
    db: Session = Depends(get_db),
):
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
    commit_and_refresh(db, template)
    return _serialize_template(template)


@router.delete("/templates/{template_id}")
def delete_template(
    template_id: int,
    current_user: AdminUser = None,
    db: Session = Depends(get_db),
):
    template = db.query(EmailTemplate).filter(EmailTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    delete_only(db, template)
    commit_only(db)
    return {"message": "Template deleted", "id": template_id}


def _serialize_template(t: EmailTemplate) -> dict:
    return {
        "id": t.id,
        "name": t.name,
        "subject": t.subject,
        "content": t.content,
        "template_type": t.template_type,
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "updated_at": t.updated_at.isoformat() if t.updated_at else None,
    }


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


@router.get("/config/runtime")
def get_email_runtime_config(current_user: AdminUser = None, db: Session = Depends(get_db)):
    cfg = db.query(EmailRuntimeConfig).order_by(EmailRuntimeConfig.id.asc()).first()
    if not cfg:
        cfg = EmailRuntimeConfig(provider="environment", smtp_port=587)
        add_and_flush(db, cfg)
        commit_and_refresh(db, cfg)
    return _email_runtime_to_dict(cfg)


@router.put("/config/runtime")
def update_email_runtime_config(
    payload: Dict[str, Any] = Body(default={}),
    current_user: AdminUser = None,
    db: Session = Depends(get_db),
):
    cfg = db.query(EmailRuntimeConfig).order_by(EmailRuntimeConfig.id.asc()).first()
    if not cfg:
        cfg = EmailRuntimeConfig()
        add_and_flush(db, cfg)
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
    commit_and_refresh(db, cfg)
    return _email_runtime_to_dict(cfg)


@router.post("/config/test-send")
def test_send_email(
    payload: Dict[str, Any] = Body(default={}),
    current_user: AdminUser = None,
    db: Session = Depends(get_db),
):
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


@public_router.get("/track/open")
async def track_open(email_id: str = Query(...), user_id: int = Query(None)):
    """Tracking pixel for email open detection."""
    try:
        from utils.email_service import record_email_delivery_event
        record_email_delivery_event(email_id=email_id, user_id=user_id, event_type="open")
    except Exception:
        pass
    return Response(content=_TRANSPARENT_GIF, media_type="image/gif")


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


@router.post("/internal", response_model=dict)
def send_internal_email(
    payload: InternalEmailPayload,
    current_user: AdminUser = None,
    db: Session = Depends(get_db),
):
    """Send an internal email and store it in the employee inbox."""
    gateway = EmailGateway(db)
    sender_id = current_user.get("id") if isinstance(current_user, dict) else None
    return gateway.send_internal_email(
        to_user_ids=payload.to,
        subject=payload.subject,
        body=payload.body,
        sender_id=sender_id or 0,
    )


@router.get("/inbox")
def get_my_inbox(
    folder: str = Query("inbox"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: AdminUser = None,
    db: Session = Depends(get_db),
):
    """Get internal emails for the current admin/staff user."""
    from services.employee_communication_service import get_inbox
    employee_id = current_user.get("id") if isinstance(current_user, dict) else 0
    return get_inbox(db, employee_id=employee_id, folder=folder, limit=limit, offset=offset)

