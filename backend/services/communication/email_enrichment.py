"""Email Enrichment — smart addressing, DLP scanning, threading, notifications."""
from __future__ import annotations

import json
import logging
import re
from typing import Optional, List, Dict, Any, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import text

from data.models import User
from data.models_employee_models import Employee
from utils.datetime_utils import utcnow as _utcnow

logger = logging.getLogger(__name__)

# Allow-listed external domains for outbound email
EXTERNAL_ALLOW_LIST: set = {"*"}  # "*" means all domains allowed; override per country
DLP_KEYWORDS: list = [
    "confidential", "privileged", "secret", "classified",
    "password", "ssn", "credit card", "passport",
]
SENSITIVE_ROLES: set = {"admin", "country_head", "country_finance"}


# ══════════════════════════════════════════════════════════════════
#  Smart Addressing Router
# ══════════════════════════════════════════════════════════════════


def resolve_address(
    db: Session,
    address: str,
) -> Tuple[str, str, Optional[int]]:
    """Resolve an email address to delivery method and recipient.
    Returns (delivery_type, email, employee_id).
    delivery_type: 'internal' | 'external'
    """
    address = address.strip().lower()

    # Search employee directory first
    emp = db.execute(
        text("""
            SELECT e.id as employee_id, u.email
            FROM employees e
            JOIN users u ON u.id = e.user_id
            WHERE LOWER(u.email) = :email
              AND e.employment_status = 'active'
            LIMIT 1
        """),
        {"email": address},
    ).mappings().first()

    if emp:
        return ("internal", address, emp["employee_id"])

    return ("external", address, None)


def resolve_recipients(
    db: Session,
    addresses: List[str],
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Resolve a list of addresses. Returns (internal_recipients, external_addresses)."""
    internal: List[Dict[str, Any]] = []
    external: List[str] = []

    for addr in addresses:
        delivery_type, email, emp_id = resolve_address(db, addr)
        if delivery_type == "internal" and emp_id:
            internal.append({"employee_id": emp_id, "email": email, "delivery": "internal"})
        else:
            external.append(addr)

    return internal, external


# ══════════════════════════════════════════════════════════════════
#  DLP Scanning
# ══════════════════════════════════════════════════════════════════


def scan_content_for_dlp(
    subject: str,
    body_html: str,
    sender_role: str,
) -> Dict[str, Any]:
    """Scan email content for DLP violations. Returns scan result."""
    violations = []
    content = f"{subject} {body_html}".lower()

    for keyword in DLP_KEYWORDS:
        if keyword in content:
            violations.append({
                "keyword": keyword,
                "severity": "high" if keyword in ("secret", "classified", "password") else "medium",
            })

    # Auto-BCC for sensitive roles
    requires_bcc = sender_role in SENSITIVE_ROLES

    return {
        "has_violations": len(violations) > 0,
        "violations": violations,
        "requires_bcc": requires_bcc,
        "is_blocked": len(violations) >= 3,  # Block if 3+ violations
    }


def check_external_allow_list(
    domain: str,
    country_code: Optional[str] = None,
) -> bool:
    """Check if a domain is allowed for external sending."""
    if "*" in EXTERNAL_ALLOW_LIST:
        return True
    return domain in EXTERNAL_ALLOW_LIST


# ══════════════════════════════════════════════════════════════════
#  Email Notifications
# ══════════════════════════════════════════════════════════════════


def send_email_notification(
    db: Session,
    recipient_employee_id: int,
    email_id: int,
    subject: str,
) -> None:
    """Trigger in-app notification for new internal email."""
    try:
        db.execute(
            text("""
                INSERT INTO notifications (user_id, type, title, message, link, created_at)
                SELECT u.id, 'email', 'New Email', :subject,
                       '/admin/employees?tab=communications&email_id=' || :email_id,
                       :now
                FROM employees e
                JOIN users u ON u.id = e.user_id
                WHERE e.id = :emp_id
            """),
            {
                "subject": subject[:100],
                "email_id": email_id,
                "emp_id": recipient_employee_id,
                "now": _utcnow(),
            },
        )
        db.commit()
    except Exception as e:
        logger.debug("Failed to send email notification: %s", e)


# ══════════════════════════════════════════════════════════════════
#  Thread Helpers
# ══════════════════════════════════════════════════════════════════


def get_or_create_thread_id(db: Session, email_id: int, in_reply_to: Optional[int] = None) -> str:
    """Get thread_id from parent email or create a new thread."""
    if in_reply_to:
        parent = db.execute(
            text("SELECT thread_id FROM internal_emails WHERE id = :id"),
            {"id": in_reply_to},
        ).scalar()
        if parent:
            return str(parent)

    # New thread — use the email's own id as thread_id
    return str(email_id)
