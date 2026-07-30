"""Email Enrichment Router — smart addressing, DLP scanning, notifications."""
from __future__ import annotations

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from controllers.auth_controller import get_current_user
from db.database import get_db
from models import User
from services.email_enrichment import (
    resolve_address,
    resolve_recipients,
    scan_content_for_dlp,
    send_email_notification,
    get_or_create_thread_id,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/address/resolve")
def api_resolve_address(
    address: str,
    db: Session = Depends(get_db),
):
    delivery_type, email, emp_id = resolve_address(db, address)
    return {
        "address": address,
        "delivery_type": delivery_type,
        "email": email,
        "employee_id": emp_id,
    }


@router.post("/address/resolve-bulk")
def api_resolve_recipients(
    addresses: List[str],
    db: Session = Depends(get_db),
):
    internal, external = resolve_recipients(db, addresses)
    return {
        "internal_recipients": internal,
        "external_addresses": external,
        "total_internal": len(internal),
        "total_external": len(external),
    }


@router.post("/dlp/scan")
def api_dlp_scan(
    subject: str,
    body_html: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sender_role = current_user.get("role", "")
    return scan_content_for_dlp(subject, body_html, sender_role)


@router.post("/notify")
def api_send_notification(
    recipient_employee_id: int,
    email_id: int,
    subject: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    send_email_notification(db, recipient_employee_id, email_id, subject)
    return {"notified": True, "employee_id": recipient_employee_id}
