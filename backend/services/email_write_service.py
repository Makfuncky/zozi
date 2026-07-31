"""Email write service — DB write operations for email entities."""

from sqlalchemy.orm import Session

from models import EmailCampaign
from models.employee_models import EmailFolder, InternalEmail


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