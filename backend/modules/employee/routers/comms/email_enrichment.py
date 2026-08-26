# === From email_enrichment.py ===
from comms.router import router  # noqa: F401
"""Email Enrichment Router — smart addressing, DLP scanning, notifications."""

import logging
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from rbac import get_current_user
from infrastructure.database.database import get_db
from domains.comms.services._auto_stubs import resolve_address
from domains.comms.services._auto_stubs import resolve_recipients
from domains.comms.services._auto_stubs import scan_content_for_dlp
from domains.comms.services._auto_stubs import send_email_notification

logger = logging.getLogger(__name__)

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


