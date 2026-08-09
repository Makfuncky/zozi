"""
Communication Domain — notifications, push tokens, mobile endpoints.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db.database import get_db
from models import Employee, Notification, PushNotificationToken
from services.attendance_service import AttendanceService
from services.expense_processing import ExpenseProcessingService
from services.leave_accrual import LeaveAccrualEngine
from services.mobile_auth_service import MobileAuthService
from utils.constants import NOTIFICATIONS_PAGE_LIMIT

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Pydantic Models ──────────────────────────────────────────────────────────


class BiometricLoginRequest(BaseModel):
    biometric_token: str
    platform: str


class CheckInRequest(BaseModel):
    lat: float
    lon: float
    office_id: Optional[int] = None


class LeaveRequest(BaseModel):
    leave_type: str
    days: float
    start_date: datetime
    end_date: datetime


class ExpenseSubmitRequest(BaseModel):
    expense_type: str
    amount: float
    currency: str = "OMR"
    expense_date: datetime
    receipt_url: Optional[str] = None


# ── Notifications ────────────────────────────────────────────────────────────


def get_notifications(current_user: dict, db: Session) -> List[Notification]:
    return (
        db.query(Notification)
        .filter(Notification.user_id == current_user["id"])
        .order_by(Notification.created_at.desc())
        .limit(NOTIFICATIONS_PAGE_LIMIT)
        .all()
    )


def mark_all_read(current_user: dict, db: Session) -> dict:
    unread_notifications = (
        db.query(Notification)
        .filter(
            Notification.user_id == current_user["id"],
            Notification.is_read == False,
        )
        .all()
    )
    for notification in unread_notifications:
        notification.is_read = True
        notification.read_at = datetime.utcnow()
    db.commit()
    return {"detail": "All notifications marked as read"}


def mark_notification_read(notification_id: int, current_user: dict, db: Session) -> Notification:
    notif = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user["id"],
    ).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    notif.is_read = True
    notif.read_at = datetime.utcnow()
    db.commit()
    db.refresh(notif)
    return notif


def delete_notification(notification_id: int, current_user: dict, db: Session) -> dict:
    notif = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user["id"],
    ).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    db.delete(notif)
    db.commit()
    return {"detail": "Notification deleted"}


def register_push_token(token: str, platform: str, device_name: str | None, current_user: dict, db: Session) -> dict:
    """Register (or re-activate) a push notification token for the current user."""
    if not token or not token.strip():
        raise HTTPException(status_code=422, detail="token is required")
    token = token.strip()
    allowed_platforms = {"expo", "fcm", "apns"}
    if platform not in allowed_platforms:
        raise HTTPException(status_code=422, detail=f"platform must be one of {sorted(allowed_platforms)}")

    user_id = int(current_user["id"])
    existing = db.query(PushNotificationToken).filter(
        PushNotificationToken.user_id == user_id,
        PushNotificationToken.token == token,
    ).first()

    if existing:
        existing.is_active = True
        existing.platform = platform
        if device_name:
            existing.device_name = device_name
        db.commit()
        return {"detail": "Push token updated", "status": "updated", "token": token}

    push_token = PushNotificationToken(
        user_id=user_id,
        token=token,
        platform=platform,
        device_name=device_name,
        is_active=True,
    )
    db.add(push_token)
    db.commit()
    return {"detail": "Push token registered", "status": "registered", "token": token}


def unregister_push_token(token: str, current_user: dict, db: Session) -> dict:
    """Deactivate a push notification token (e.g. on logout)."""
    user_id = int(current_user["id"])
    row = db.query(PushNotificationToken).filter(
        PushNotificationToken.user_id == user_id,
        PushNotificationToken.token == token,
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="Push token not found")
    row.is_active = False
    db.commit()
    return {"detail": "Push token unregistered", "status": "unregistered", "token": token}


# ── Mobile Endpoints ─────────────────────────────────────────────────────────


@router.post("/mobile/biometric-login")
def biometric_login(
    request: BiometricLoginRequest,
    current_user: dict,
    db: Session = Depends(get_db),
):
    service = MobileAuthService(db)
    return service.validate_biometric(
        current_user.get("id"),
        request.biometric_token,
        request.platform,
    )


@router.post("/mobile/check-in")
def mobile_check_in(
    request: CheckInRequest,
    current_user: dict,
    db: Session = Depends(get_db),
):
    service = MobileAuthService(db)
    return service.geo_fenced_check_in(
        current_user.get("id"),
        request.lat,
        request.lon,
        request.office_id,
    )


@router.get("/mobile/leave-balance")
def get_leave_balance(
    current_user: dict,
    db: Session = Depends(get_db),
):
    engine = LeaveAccrualEngine(db)
    employee = db.query(Employee).filter(Employee.user_id == current_user.get("id")).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return engine.get_balance(employee.id)


@router.post("/mobile/expenses")
def submit_expense(
    request: ExpenseSubmitRequest,
    current_user: dict,
    db: Session = Depends(get_db),
):
    service = ExpenseProcessingService(db)
    employee = db.query(Employee).filter(Employee.user_id == current_user.get("id")).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    return service.submit_expense(
        employee_id=employee.id,
        expense_type=request.expense_type,
        amount=request.amount,
        currency=request.currency,
        expense_date=request.expense_date,
        receipt_url=request.receipt_url,
    )
