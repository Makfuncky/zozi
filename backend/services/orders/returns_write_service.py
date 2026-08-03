"""Returns write service — DB write operations for return requests and notifications."""

from typing import Optional

from sqlalchemy.orm import Session

from data.models import (
    Notification,
    ReturnRequest,
)


def get_return_by_id(db: Session, return_id: int) -> Optional[ReturnRequest]:
    """Fetch a single ReturnRequest by ID."""
    return db.query(ReturnRequest).filter(ReturnRequest.id == return_id).first()


def create_return_request(db: Session, **return_request_data) -> ReturnRequest:
    return_request = ReturnRequest(**return_request_data)
    db.add(return_request)
    db.commit()
    db.refresh(return_request)
    return return_request


def update_return_request(db: Session, return_request: ReturnRequest, updates: dict) -> ReturnRequest:
    for key, value in updates.items():
        setattr(return_request, key, value)
    db.commit()
    db.refresh(return_request)
    return return_request


def create_return_notification(db: Session, **notification_data) -> Notification:
    notification = Notification(**notification_data)
    db.add(notification)
    db.commit()
    return notification