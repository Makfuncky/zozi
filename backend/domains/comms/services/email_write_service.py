"""Email write service — DB write operations for email entities."""
from __future__ import annotations

from typing import List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session

from domains.comms.models.communication import EmailFolder
from domains.comms.models.communication import InternalEmail
from domains.comms.models.marketing import EmailCampaign
from domains.hr.models.employee_models import Employee
from domains.accounts.models.user import User
from sqlalchemy import func, desc
from infrastructure.utils.pagination import SAFE_QUERY_LIMIT
from infrastructure.utils.datetime_utils import utcnow as _utcnow

from domains.comms.models.marketing import EmailTemplate
from domains.comms.models.marketing import EmailRuntimeConfig
from domains.comms.models.marketing import EmailSuppression
import structlog
logger = structlog.get_logger(__name__)


def create_email_campaign(db: Session, **campaign_data) -> EmailCampaign:
    campaign = EmailCampaign(**campaign_data)
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return campaign


def delete_email_campaign(db: Session, campaign: EmailCampaign) -> None:
    db.delete(campaign)
    db.commit()


def create_email_folder(db: Session, employee_id: int, name: str, icon: str = None, sort_order: int = 0) -> EmailFolder:
    folder = EmailFolder(
        employee_id=employee_id,
        name=name,
        folder_type="custom",
        icon=icon,
        sort_order=sort_order,
        is_system=False,
    )
    db.add(folder)
    db.commit()
    db.refresh(folder)
    return folder


def update_internal_email_folder(db: Session, email: InternalEmail, folder_id: int) -> InternalEmail:
    email.folder_id = folder_id
    db.commit()
    db.refresh(email)
    return email


def rename_email_folder(db: Session, folder: EmailFolder, new_name: str) -> EmailFolder:
    folder.name = new_name
    db.commit()
    db.refresh(folder)
    return folder


def delete_email_folder(db: Session, folder: EmailFolder, employee_id: int = None) -> None:
    if employee_id:
        inbox = db.query(EmailFolder).filter(
            EmailFolder.employee_id == employee_id, EmailFolder.name == "inbox"
        ).first()
        if inbox:
            db.query(InternalEmail).filter(InternalEmail.folder_id == folder.id).update(
                {"folder_id": inbox.id}
            )
    db.delete(folder)
    db.commit()


def get_employee_by_user_id(db: Session, user_id: int) -> Optional[Employee]:
    """Get employee record by user ID."""
    return db.query(Employee).filter(Employee.user_id == user_id).first()


def get_user_folders_with_counts(db: Session, user_id: int) -> List[dict]:
    """List folders with email counts for a user."""
    folders = db.query(EmailFolder).filter(EmailFolder.employee_id == user_id).limit(SAFE_QUERY_LIMIT).all()
    # N+1 removal: aggregate all folder counts in a single grouped query before the loop.
    folder_ids = [folder.id for folder in folders]
    counts_by_folder: dict = {}
    if folder_ids:
        count_rows = (
            db.query(InternalEmail.folder_id, func.count(InternalEmail.id))
            .filter(InternalEmail.folder_id.in_(folder_ids))
            .group_by(InternalEmail.folder_id)
            .limit(SAFE_QUERY_LIMIT)
            .all()
        )
        counts_by_folder = {row[0]: row[1] for row in count_rows}
    result = []
    for folder in folders:
        email_count = counts_by_folder.get(folder.id) or 0
        result.append({
            "id": folder.id,
            "name": folder.name,
            "folder_type": folder.folder_type,
            "email_count": email_count,
        })
    return result


def create_user_folder(db: Session, user_id: int, name: str, icon: str = None) -> EmailFolder:
    """Create a folder for a user."""
    return create_email_folder(db, user_id, name, icon)


def move_email_to_folder(db: Session, email_id: int, folder_id: int, user_id: int) -> InternalEmail:
    """Move an email to a different folder."""
    email = db.query(InternalEmail).filter(InternalEmail.id == email_id).first()
    if not email:
        raise ValueError("Email not found")
    email.folder_id = folder_id
    db.commit()
    db.refresh(email)
    return email


def rename_user_folder(db: Session, folder: EmailFolder, new_name: str, user_id: int) -> EmailFolder:
    """Rename a user's folder."""
    if folder.employee_id != user_id:
        raise ValueError("Access denied")
    folder.name = new_name
    db.commit()
    db.refresh(folder)
    return folder


def delete_user_folder(db: Session, folder_id: int, user_id: int) -> None:
    """Delete a user's folder."""
    folder = db.query(EmailFolder).filter(
        EmailFolder.id == folder_id,
        EmailFolder.employee_id == user_id,
        EmailFolder.folder_type == "custom"
    ).first()
    if not folder:
        raise ValueError("Folder not found or access denied")
    db.delete(folder)
    db.commit()


def get_users_by_emails(db: Session, emails: List[str]) -> List[User]:
    """Find users by email addresses."""
    return db.query(User).filter(User.email.in_(emails)).limit(SAFE_QUERY_LIMIT).all()


def get_folder_by_id(db: Session, folder_id: int) -> Optional[EmailFolder]:
    """Look up a single EmailFolder by ID."""
    return db.query(EmailFolder).filter(EmailFolder.id == folder_id).first()


def get_internal_email_by_id(db: Session, email_id: int) -> Optional[InternalEmail]:
    """Look up a single InternalEmail by ID."""
    return db.query(InternalEmail).filter(InternalEmail.id == email_id).first()


def list_folders_paginated(
    db: Session, user_id: int, skip: int = 0, limit: int = 20
) -> dict:
    """List folders with email counts and unread counts, paginated."""
    emp = get_employee_by_user_id(db, user_id)
    if not emp:
        return {"employee": None}

    q = (
        db.query(EmailFolder)
        .filter(EmailFolder.employee_id == emp.id)
        .order_by(EmailFolder.sort_order, EmailFolder.name)
    )
    total = q.count()
    folders = q.offset(skip).limit(limit).all()

    # N+1 removal: aggregate total/unread counts in two grouped queries before the loop.
    folder_ids = [f.id for f in folders]
    counts_by_folder: dict = {}
    unread_by_folder: dict = {}
    if folder_ids:
        count_rows = (
            db.query(InternalEmail.folder_id, func.count(InternalEmail.id))
            .filter(InternalEmail.folder_id.in_(folder_ids))
            .group_by(InternalEmail.folder_id)
            .limit(SAFE_QUERY_LIMIT)
            .all()
        )
        counts_by_folder = {row[0]: row[1] for row in count_rows}
        unread_rows = (
            db.query(InternalEmail.folder_id, func.count(InternalEmail.id))
            .filter(
                InternalEmail.folder_id.in_(folder_ids),
                InternalEmail.is_read == False,
            )
            .group_by(InternalEmail.folder_id)
            .limit(SAFE_QUERY_LIMIT)
            .all()
        )
        unread_by_folder = {row[0]: row[1] for row in unread_rows}

    result = []
    for f in folders:
        count = counts_by_folder.get(f.id) or 0
        unread = unread_by_folder.get(f.id) or 0
        result.append({
            "id": f.id,
            "name": f.name,
            "folder_type": f.folder_type,
            "icon": f.icon,
            "sort_order": f.sort_order,
            "is_system": f.is_system,
            "count": count,
            "unread": unread,
        })

    return {"total": total, "folders": result}


def get_folder_by_id_and_employee(db: Session, folder_id: int, employee_id: int) -> Optional[EmailFolder]:
    """Look up a folder scoped to an employee for ownership checks."""
    return db.query(EmailFolder).filter(
        EmailFolder.id == folder_id,
        EmailFolder.employee_id == employee_id,
    ).first()


def find_folder_by_name_and_employee(
    db: Session, employee_id: int, name: str, exclude_id: Optional[int] = None
) -> Optional[EmailFolder]:
    """Find a folder by name within an employee's folders (for duplicate checks)."""
    q = db.query(EmailFolder).filter(
        EmailFolder.employee_id == employee_id,
        EmailFolder.name == name,
    )
    if exclude_id is not None:
        q = q.filter(EmailFolder.id != exclude_id)
    return q.first()


def get_max_folder_sort_order(db: Session, employee_id: int) -> int:
    """Return the highest sort_order currently in use by an employee's folders."""
    max_order = (
        db.query(EmailFolder.sort_order)
        .filter(EmailFolder.employee_id == employee_id)
        .order_by(EmailFolder.sort_order.desc())
        .first()
    )
    return (max_order[0] + 1) if max_order and max_order[0] is not None else 0


def list_dlp_violations(db: Session, status: Optional[str] = None, limit: int = 50, offset: int = 0) -> List[dict]:
    """List DLP violations."""
    query = db.query(EmailCampaign).filter(
        EmailCampaign.campaign_type == "dlp_violation"
    )
    if status:
        query = query.filter(EmailCampaign.status == status)
    violations = query.order_by(EmailCampaign.created_at.desc()).offset(offset).limit(limit).all()
    return [
        {
            "id": v.id,
            "campaign_type": v.campaign_type,
            "status": v.status,
            "created_at": v.created_at,
            "details": v.details,
        }
        for v in violations
    ]


_RUNTIME_SIMPLE_FIELDS = [
    "provider", "smtp_host", "smtp_port", "smtp_username",
    "smtp_use_tls", "smtp_use_ssl", "smtp_timeout_seconds",
    "email_from_default", "email_from_promotional", "email_from_transactional",
    "email_from_notification", "email_from_alert", "email_from_verification",
    "email_from_login_verification", "email_from_password_reset",
]


def apply_suppression_update(db: Session, suppression: EmailSuppression, body: dict) -> None:
    """Apply a partial suppression update and commit (router keeps serialization)."""
    if "status" in body:
        suppression.status = body["status"]
        if body["status"] == "active" and not suppression.suppressed_at:
            suppression.suppressed_at = _utcnow()
        suppression.last_event_at = _utcnow()
    if "reason" in body:
        suppression.reason = body["reason"]
    if "notes" in body:
        suppression.notes = body["notes"]
    db.commit()


def create_email_template(db: Session, **template_data) -> EmailTemplate:
    """Persist a new email template."""
    template = EmailTemplate(**template_data)
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


def update_email_template(db: Session, template: EmailTemplate, payload: dict) -> None:
    """Apply a partial template update and commit (router keeps serialization)."""
    for field in ("name", "subject", "content", "template_type"):
        if field in payload:
            setattr(template, field, payload[field])
    db.commit()
    db.refresh(template)


def delete_email_template(db: Session, template: EmailTemplate) -> None:
    """Delete an email template and commit."""
    db.delete(template)
    db.commit()


def upsert_email_runtime_config(db: Session, payload: dict) -> EmailRuntimeConfig:
    """Get-or-create the singleton runtime config, apply payload, and commit."""
    cfg = db.query(EmailRuntimeConfig).order_by(EmailRuntimeConfig.id.asc()).first()
    if not cfg:
        cfg = EmailRuntimeConfig()
        db.add(cfg)
    for field in _RUNTIME_SIMPLE_FIELDS:
        if field in payload:
            setattr(cfg, field, payload[field])
    if payload.get("resend_api_key"):
        cfg.resend_api_key = payload["resend_api_key"]
    if payload.get("resend_webhook_secret"):
        cfg.resend_webhook_secret = payload["resend_webhook_secret"]
    if payload.get("smtp_password"):
        cfg.smtp_password = payload["smtp_password"]
    db.commit()
    db.refresh(cfg)
    return cfg