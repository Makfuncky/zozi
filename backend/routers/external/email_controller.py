"""
Email Gateway Router
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from models import User
from models.employee_models import Employee
try:
    from models.communication import EmailFolder, InternalEmail
except ImportError:
    EmailFolder = None  # type: ignore[assignment,misc]
    InternalEmail = None  # type: ignore[assignment,misc]
from routers.auth import get_current_user
from services.email_gateway import get_email_gateway
from services.email_write_service import (
    create_email_folder,
    delete_email_folder,
    rename_email_folder,
    update_internal_email_folder,
)
from utils.dependencies import get_db, require_admin

logger = logging.getLogger("zozi.api.email")
router = APIRouter()


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


@router.post("/internal")
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


@router.post("/internal-by-email")
def send_internal_email_by_email(
    payload: SendInternalEmailByEmailPayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Send an internal email using email addresses instead of user IDs.
    ComposerDock's email mode calls this endpoint.
    """
    # Look up users by their email addresses
    users = db.query(User).filter(User.email.in_(payload.to)).all()
    if not users:
        raise HTTPException(
            status_code=404,
            detail="No users found matching the provided email addresses",
        )
    to_user_ids = [u.id for u in users]

    # Resolve CC recipients
    if payload.cc:
        cc_users = db.query(User).filter(User.email.in_(payload.cc)).all()
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


@router.post("/external")
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


@router.get("/templates")
def get_templates(db: Session = Depends(get_db)):
    email = get_email_gateway(db)
    return {"templates": email.get_email_templates()}


@router.post("/track-open")
def track_open(email_id: str, user_id: int, db: Session = Depends(get_db)):
    email = get_email_gateway(db)
    return email.track_open(email_id, user_id)


@router.get("/history/{user_id}")
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


@router.get("/folders")
def list_folders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all email folders for the current user, with email counts."""
    emp = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee profile not found")

    folders = (
        db.query(EmailFolder)
        .filter(EmailFolder.employee_id == emp.id)
        .order_by(EmailFolder.sort_order, EmailFolder.name)
        .all()
    )

    result = []
    for f in folders:
        count = (
            db.query(InternalEmail)
            .filter(InternalEmail.folder_id == f.id)
            .count()
        )
        unread = (
            db.query(InternalEmail)
            .filter(InternalEmail.folder_id == f.id, InternalEmail.is_read == False)
            .count()
        )
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

    return {"folders": result}


@router.post("/folders")
def create_folder(
    payload: CreateFolderPayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a custom email folder."""
    emp = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee profile not found")

    existing = (
        db.query(EmailFolder)
        .filter(EmailFolder.employee_id == emp.id, EmailFolder.name == payload.name)
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Folder with this name already exists")

    max_order = (
        db.query(EmailFolder.sort_order)
        .filter(EmailFolder.employee_id == emp.id)
        .order_by(EmailFolder.sort_order.desc())
        .first()
    )
    next_order = (max_order[0] + 1) if max_order and max_order[0] is not None else 0

    folder = create_email_folder(db, emp.id, payload.name, payload.icon, next_order)

    return {
        "id": folder.id,
        "name": folder.name,
        "folder_type": folder.folder_type,
        "icon": folder.icon,
        "sort_order": folder.sort_order,
        "is_system": folder.is_system,
        "count": 0,
        "unread": 0,
    }


@router.put("/folders/{email_id}/move")
def move_email(
    email_id: int,
    payload: MoveEmailPayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Move an internal email to a different folder."""
    email = db.query(InternalEmail).filter(InternalEmail.id == email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    folder = db.query(EmailFolder).filter(EmailFolder.id == payload.folder_id).first()
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")

    # Verify ownership: user must be sender or recipient
    recipients = email.recipients or []
    recipient_ids = [r.get("user_id") for r in recipients if isinstance(r, dict)]
    if email.sender_id != current_user.id and current_user.id not in recipient_ids:
        raise HTTPException(status_code=403, detail="You do not have access to this email")

    old_folder_id = email.folder_id
    email = update_internal_email_folder(db, email, payload.folder_id)

    return {
        "success": True,
        "email_id": email.id,
        "old_folder_id": old_folder_id,
        "new_folder_id": email.folder_id,
    }


@router.patch("/folders/{folder_id}")
def rename_folder(
    folder_id: int,
    payload: RenameFolderPayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Rename a custom folder. System folders cannot be renamed."""
    folder = db.query(EmailFolder).filter(EmailFolder.id == folder_id).first()
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    if folder.is_system:
        raise HTTPException(status_code=400, detail="Cannot rename system folders")

    new_name = payload.name.strip()
    if not new_name:
        raise HTTPException(status_code=422, detail="Folder name cannot be empty")

    # Check for duplicate name within the same employee's folders
    dup = (
        db.query(EmailFolder)
        .filter(
            EmailFolder.employee_id == folder.employee_id,
            EmailFolder.name == new_name,
            EmailFolder.id != folder_id,
        )
        .first()
    )
    if dup:
        raise HTTPException(status_code=409, detail="A folder with this name already exists")

    old_name = folder.name
    folder = rename_email_folder(db, folder, new_name)

    return {
        "success": True,
        "folder_id": folder.id,
        "old_name": old_name,
        "new_name": folder.name,
    }


@router.delete("/folders/{folder_id}")
def delete_folder(
    folder_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a custom folder. System folders cannot be deleted."""
    folder = db.query(EmailFolder).filter(EmailFolder.id == folder_id).first()
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    if folder.is_system:
        raise HTTPException(status_code=400, detail="Cannot delete system folders")

    delete_email_folder(db, folder, folder.employee_id)

    return {"success": True, "deleted_folder_id": folder_id}


@router.get("/directory")
def employee_directory(
    search: Optional[str] = None,
    country_code: Optional[str] = None,
    department: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """Search employee directory for the compose recipient picker."""
    from services.employee_communication_service import get_employee_directory
    return get_employee_directory(db, search=search, country_code=country_code, department=department, limit=limit)


@router.get("/dlp-violations")
def list_dlp_violations(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
):
    """List DLP violations for admin review."""
    from models.fraud import DLPViolation
    q = db.query(DLPViolation).order_by(DLPViolation.created_at.desc())
    if status:
        q = q.filter(DLPViolation.status == status)
    total = q.count()
    violations = q.offset(offset).limit(limit).all()
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "violations": [
            {
                "id": v.id,
                "violation_type": v.violation_type,
                "severity": v.severity,
                "sender_id": v.sender_id,
                "recipient_email": v.recipient_email,
                "detected_content": v.detected_content,
                "action_taken": v.action_taken,
                "status": v.status,
                "created_at": v.created_at.isoformat() if v.created_at else None,
            }
            for v in violations
        ],
    }
