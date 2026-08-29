"""Compliance service — GDPR export, anonymisation, and hard-delete helpers.

All operations are scoped to a single ``user_id`` and operate over data the
customers domain owns (or can read via Law 3 ports). ``export_user_data``
returns a JSON-serialisable bundle, ``anonymize_user_id`` strips PII from the
``accounts.users`` row and related customer-side data, and ``delete_user_data``
performs a hard delete (cascades apply via FKs).
"""
from __future__ import annotations

from typing import Any, Dict, List

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from domains.accounts.ports import Address, User, UserSession
from domains.customers.models import CustomerPreference, CustomerTag, NotificationPreference
from domains.orders.ports import Order
from infrastructure.utils.datetime_utils import utcnow
import structlog

logger = structlog.get_logger(__name__)


def _user_exists(db: Session, user_id: int) -> bool:
    return db.query(User.id).filter(User.id == int(user_id)).first() is not None


def _serialize_user(user: User) -> Dict[str, Any]:
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "country_code": user.country_code,
        "is_active": user.is_active,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
    }


class ComplianceService:
    """Service facade for GDPR export, anonymise, and delete operations."""

    def __init__(self, db: Session):
        self.db = db

    def export_user_data(self, user_id: int) -> Dict[str, Any]:
        """Bundle all GDPR-relevant data for ``user_id`` into one snapshot."""
        user = self.db.query(User).filter(User.id == int(user_id)).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )
        addresses: List[Dict[str, Any]] = [
            {
                "id": a.id,
                "label": getattr(a, "label", None),
                "address_line1": a.address_line1,
                "address_line2": a.address_line2,
                "city": a.city,
                "state": a.state,
                "postal_code": a.postal_code,
                "country": a.country,
                "is_default": a.is_default,
            }
            for a in self.db.query(Address).filter(Address.user_id == int(user_id)).limit(1000).all()
        ]
        orders: List[Dict[str, Any]] = [
            {
                "id": o.id,
                "order_number": o.order_number,
                "status_code": o.status_code,
                "payment_status": o.payment_status,
                "total_amount": o.total_amount,
                "currency": o.currency,
                "created_at": o.created_at,
            }
            for o in self.db.query(Order).filter(Order.user_id == int(user_id)).limit(1000).all()
        ]
        preferences = (
            self.db.query(CustomerPreference)
            .filter(
                CustomerPreference.user_id == int(user_id),
                CustomerPreference.is_deleted.is_(False),
            )
            .all()
        )
        notif_prefs = (
            self.db.query(NotificationPreference)
            .filter(
                NotificationPreference.user_id == int(user_id),
                NotificationPreference.is_deleted.is_(False),
            )
            .all()
        )
        tags = (
            self.db.query(CustomerTag)
            .filter(
                CustomerTag.user_id == int(user_id),
                CustomerTag.is_deleted.is_(False),
            )
            .all()
        )
        return {
            "user_id": int(user_id),
            "exported_at": utcnow(),
            "user": _serialize_user(user),
            "addresses": addresses,
            "orders": orders,
            "preferences": [
                {"key": p.key, "value": p.value, "updated_at": p.updated_at}
                for p in preferences
            ],
            "notification_preferences": [
                {
                    "channel": n.channel,
                    "topic": n.topic,
                    "enabled": n.enabled,
                    "updated_at": n.updated_at,
                }
                for n in notif_prefs
            ],
            "tags": [t.tag for t in tags],
        }

    def anonymize_user_id(self, user_id: int) -> Dict[str, Any]:
        """Strip PII from a user account and related customer-side rows."""
        user = self.db.query(User).filter(User.id == int(user_id)).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )
        redacted_email = f"anon-{user.id}@deleted.invalid"
        user.email = redacted_email
        user.full_name = None
        user.is_active = False
        user.staff_country_codes = None
        self.db.add(user)

        self.db.query(CustomerPreference).filter(
            CustomerPreference.user_id == int(user_id)
        ).update({CustomerPreference.value: None, CustomerPreference.is_deleted: True})
        self.db.query(NotificationPreference).filter(
            NotificationPreference.user_id == int(user_id)
        ).update({NotificationPreference.is_deleted: True})
        self.db.query(CustomerTag).filter(
            CustomerTag.user_id == int(user_id)
        ).update({CustomerTag.is_deleted: True})

        for addr in self.db.query(Address).filter(Address.user_id == int(user_id)).limit(1000).all():
            addr.address_line1 = "[redacted]"
            addr.address_line2 = None
            addr.city = None
            addr.state = None
            addr.postal_code = None
            addr.full_name = None
            addr.phone = None
            self.db.add(addr)

        try:
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            logger.error("compliance.anonymize_failed", user_id=user_id, error=str(exc))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to anonymize user.",
            ) from exc
        return {
            "user_id": int(user_id),
            "anonymized_at": utcnow(),
            "email": redacted_email,
        }

    def delete_user_data(self, user_id: int) -> Dict[str, Any]:
        """Hard-delete the user record and cascade dependent rows."""
        if not _user_exists(self.db, user_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )
        self.db.query(CustomerPreference).filter(
            CustomerPreference.user_id == int(user_id)
        ).delete(synchronize_session=False)
        self.db.query(NotificationPreference).filter(
            NotificationPreference.user_id == int(user_id)
        ).delete(synchronize_session=False)
        self.db.query(CustomerTag).filter(
            CustomerTag.user_id == int(user_id)
        ).delete(synchronize_session=False)
        self.db.query(Address).filter(
            Address.user_id == int(user_id)
        ).delete(synchronize_session=False)
        self.db.query(UserSession).filter(
            UserSession.user_id == int(user_id)
        ).delete(synchronize_session=False)
        self.db.query(User).filter(User.id == int(user_id)).delete(synchronize_session=False)
        try:
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            logger.error("compliance.delete_failed", user_id=user_id, error=str(exc))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete user.",
            ) from exc
        return {
            "user_id": int(user_id),
            "deleted_at": utcnow(),
        }
