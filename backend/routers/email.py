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

from data.controllers_admin_controller import require_roles
from data.db import get_db
from routers.auth import get_current_user
from services.communication.email_gateway import EmailGateway
from services.communication.transactional_email_service import (
    enqueue_order_created_email,
    enqueue_invoice_email,
    enqueue_low_stock_alert_email,
    enqueue_order_confirmation_email,
)
from services.communication.email_management_service import (
    EmailManagementService,
    get_email_management_service,
)

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


def _get_svc(db: Session = Depends(get_db)) -> EmailManagementService:
    return EmailManagementService(db)


@public_router.post("/webhooks/resend")
async def resend_webhook(request: Request):
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
    svc: EmailManagementService = Depends(_get_svc),
):
    return svc.list_templates(skip=skip, limit=limit)


@router.get("/campaigns")
def list_campaigns(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: AdminUser = None,
    svc: EmailManagementService = Depends(_get_svc),
):
    return svc.list_campaigns(skip=skip, limit=limit)


@router.get("/suppressions")
def list_suppressions(
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: AdminOrSuperAdminUser = None,
    svc: EmailManagementService = Depends(_get_svc),
):
    return svc.list_suppressions(status=status, skip=skip, limit=limit)


@router.patch("/suppressions/{suppression_id}")
def update_suppression(
    suppression_id: int,
    body: Dict[str, Any] = Body(default={}),
    current_user: AdminOrSuperAdminUser = None,
    svc: EmailManagementService = Depends(_get_svc),
):
    try:
        return svc.update_suppression(suppression_id, body)
    except ValueError:
        raise HTTPException(status_code=404, detail="Suppression not found")


@router.post("/campaigns")
def create_campaign(
    payload: Dict[str, Any] = Body(default={}),
    current_user: AdminUser = None,
    svc: EmailManagementService = Depends(_get_svc),
):
    user_id = current_user.get("id") if isinstance(current_user, dict) else None
    return svc.create_campaign(payload, user_id=user_id)


@router.post("/templates")
def create_template(
    payload: Dict[str, Any] = Body(default={}),
    current_user: AdminUser = None,
    svc: EmailManagementService = Depends(_get_svc),
):
    user_id = current_user.get("id") if isinstance(current_user, dict) else None
    return svc.create_template(payload, user_id=user_id)


@router.put("/templates/{template_id}")
def update_template(
    template_id: int,
    payload: Dict[str, Any] = Body(default={}),
    current_user: AdminUser = None,
    svc: EmailManagementService = Depends(_get_svc),
):
    try:
        return svc.update_template(template_id, payload)
    except ValueError:
        raise HTTPException(status_code=404, detail="Template not found")


@router.delete("/templates/{template_id}")
def delete_template(
    template_id: int,
    current_user: AdminUser = None,
    svc: EmailManagementService = Depends(_get_svc),
):
    try:
        return svc.delete_template(template_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Template not found")


@router.get("/config/runtime")
def get_email_runtime_config(
    current_user: AdminUser = None,
    svc: EmailManagementService = Depends(_get_svc),
):
    return svc.get_email_runtime_config()


@router.put("/config/runtime")
def update_email_runtime_config(
    payload: Dict[str, Any] = Body(default={}),
    current_user: AdminUser = None,
    svc: EmailManagementService = Depends(_get_svc),
):
    return svc.update_email_runtime_config(payload)


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
