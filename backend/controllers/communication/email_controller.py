"""
Email Gateway Controller
"""
import logging
from typing import List, Optional

from fastapi import Depends, HTTPException, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel

from dependencies.db import get_db
from models import User
from routers.security.auth import get_current_user
from utils.dependencies import require_admin
from services.communication.email_gateway import EmailGateway, get_email_gateway
from services.communication.email_write_service import (
    get_employee_by_user_id,
    get_user_folders_with_counts,
    create_user_folder,
    move_email_to_folder,
    rename_user_folder,
    delete_user_folder,
    get_users_by_emails,
    list_dlp_violations as get_dlp_violations,
)

logger = logging.getLogger("zozi.api.email")


class SendInternalEmailPayload(BaseModel):
    to: List[int]
    subject: str
    body: str


class SendInternalEmailByEmailPayload(BaseModel):
    to: List[str]
    subject: str
    body: str
    cc: Optional[List[str]] = None
    in_reply_to: Optional[int] = None


def send_internal_email(
    payload: SendInternalEmailPayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    email = get_email_gateway(db)
    return email.send_internal_email(
        to_user_ids=payload.to,
        subject=payload.subject,
        body=payload.body,
        sender_id=current_user.id,
    )


def send_internal_email_by_email(
    payload: SendInternalEmailByEmailPayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Send an internal email using email addresses instead of user IDs.
    ComposerDock's email mode calls this endpoint.
    """
    to_users = get_users_by_emails(db, payload.to)
    if not to_users:
        raise HTTPException(
            status_code=404,
            detail="No users found matching the provided email addresses",
        )
    to_user_ids = [u.id for u in to_users]

    if payload.cc:
        cc_users = get_users_by_emails(db, payload.cc)
        cc_ids = [u.id for u in cc_users]
        to_user_ids.extend(cc_ids)

    gateway = get_email_gateway(db)
    return gateway.send_internal_email(
        to_user_ids=list(set(to_user_ids)),
        subject=payload.subject,
        body=payload.body,
        sender_id=current_user.id,
        in_reply_to=payload.in_reply_to,
    )


def send_external_email(
    to: str = Body(...),
    subject: str = Body(...),
    body: str = Body(...),
    template_id: Optional[str] = Body(None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    email = get_email_gateway(db)
    return email.send_external_email(to, subject, body, current_user["id"], template_id)


def get_templates(db: Session = Depends(get_db)):
    email = get_email_gateway(db)
    return {"templates": email.get_email_templates()}


def track_open(email_id: str, user_id: int, db: Session = Depends(get_db)):
    email = get_email_gateway(db)
    return email.track_open(email_id, user_id)


def get_email_history(
    user_id: int,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    email = get_email_gateway(db)
    return email.get_email_history(user_id, limit, offset)


# ── Folder Management ────────────────────────────────────────────────

class CreateFolderPayload(BaseModel):
    name: str
    icon: Optional[str] = None

class MoveEmailPayload(BaseModel):
    folder_id: int

class RenameFolderPayload(BaseModel):
    name: str


def list_folders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all email folders for the current user, with email counts."""
    return get_user_folders_with_counts(db, current_user.id)


def create_folder(
    payload: CreateFolderPayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a custom email folder."""
    emp = get_employee_by_user_id(db, current_user.id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee profile not found")
    return create_user_folder(db, emp.id, payload.name, payload.icon)


def move_email(
    email_id: int,
    payload: MoveEmailPayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Move an internal email to a different folder."""
    return move_email_to_folder(db, email_id, payload.folder_id, current_user.id)


def rename_folder(
    folder_id: int,
    payload: RenameFolderPayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Rename a custom folder. System folders cannot be renamed."""
    return rename_user_folder(db, folder_id, payload.name, current_user.id)


def delete_folder(
    folder_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a custom folder. System folders cannot be deleted."""
    return delete_user_folder(db, folder_id, current_user.id)


def employee_directory(
    search: Optional[str] = None,
    country_code: Optional[str] = None,
    department: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """Search employee directory for the compose recipient picker."""
    from services.hr.employee_communication_service import get_employee_directory
    return get_employee_directory(db, search=search, country_code=country_code, department=department, limit=limit)


def list_dlp_violations(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
):
    """List DLP violations for admin review."""
    return get_dlp_violations(db, status=status, limit=limit, offset=offset)

